﻿using Newtonsoft.Json;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Input;
using Newtonsoft.Json.Linq;
using StardewSpeak.Pathfinder;
using StardewModdingAPI;
using StardewValley;
using StardewValley.Objects;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using StardewValley.Menus;
using System.Reflection;
using System.Collections.Concurrent;

namespace StardewSpeak
{
    public class SpeechEngine
    {
        Process Proc;
        private readonly object StandardInLock;
        public readonly object RequestQueueLock;
        public ConcurrentQueue<dynamic> UpdateTickedRequestQueue;
        public ConcurrentQueue<dynamic> UpdateTickingRequestQueue;
        public readonly Action<Process, TaskCompletionSource<int>> OnExit;
        public HashSet<string> UnvalidatedModeAllowableMessageTypes = new HashSet<string> { 
            "HEARTBEAT", "REQUEST_BATCH", "NEW_STREAM", "STOP_STREAM", "GET_ACTIVE_MENU", "GET_MOUSE_POSITION",
            "SET_MOUSE_POSITION", "SET_MOUSE_POSITION_RELATIVE", "MOUSE_CLICK", "UPDATE_HELD_BUTTONS", "RELEASE_ALL_KEYS",
            "PRESS_KEY"
        };
        public bool Running = false;

        public SpeechEngine(Action<Process, TaskCompletionSource<int>> onExit)
        {
            this.OnExit = onExit;
            this.StandardInLock = new object();
            this.RequestQueueLock = new object();
            this.UpdateTickedRequestQueue = new ConcurrentQueue<dynamic>();
            this.UpdateTickingRequestQueue = new ConcurrentQueue<dynamic>();
        }

        public void LaunchProcess()
        {
            string rootDir = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            #if DEBUG
                ModEntry.Log("Running Python client in debug mode", LogLevel.Trace);
                string pythonRoot = Path.Combine(rootDir, @"StardewSpeak\lib\speech-client");
                string executable = Path.Combine(pythonRoot, @"Scripts\python.exe");
                string main = Path.Combine(pythonRoot, @"speech-client\main.py");
                string arguments = $"\"{main}\" --python_root \"{pythonRoot}\"";
#else
                ModEntry.Log("Running Python client in release mode", LogLevel.Trace);
                string pythonRoot = Path.Combine(rootDir, @"lib\speech-client\dist");
                string executable = Path.Combine(pythonRoot, @"speech-client.exe");
                string arguments = $"--python_root \"{pythonRoot}\"";
#endif
            Task.Factory.StartNew(() => RunProcessAsync("\"" + executable + "\"", arguments));
        }

        public async Task<int> RunProcessAsync(string fileName, string args)
        {
            using (this.Proc = new Process
            {
                StartInfo =
                {
                    FileName = fileName,
                    Arguments = args,
                    UseShellExecute = false,
                    CreateNoWindow = true,

                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    RedirectStandardInput = true,
                },
                EnableRaisingEvents = true
            })
            {
                this.Running = true;
                var proc = await RunProcessAsync(this.Proc).ConfigureAwait(false);
                return proc;
            }
        }

        public void Exit() 
        {
            try
            {
                Proc.Kill();
            }
            catch (SystemException e) { }
        }

        private void HandleExited(Process process, TaskCompletionSource<int> tcs)
        {
            this.Running = false;
            tcs.SetResult(process.ExitCode);
            this.OnExit(process, tcs);
        }
        private Task<int> RunProcessAsync(Process process)
        {
            var tcs = new TaskCompletionSource<int>();

            process.Exited += (s, ea) => HandleExited(process, tcs);
            process.OutputDataReceived += (s, ea) => this.OnMessage(ea.Data);
            process.ErrorDataReceived += (s, ea) => this.onError("ERR: " + ea.Data);

            bool started = process.Start();
            if (!started)
            {
                //you may allow for the process to be re-used (started = false) 
                //but I'm not sure about the guarantees of the Exited event in such a case
                throw new InvalidOperationException("Could not start process: " + process);
            }

            process.BeginOutputReadLine();
            process.BeginErrorReadLine();
            return tcs.Task;
        }

        void OnMessage(string messageText)
        {
            dynamic msg;
            try
            {
                msg = JsonConvert.DeserializeObject(messageText);
            }
            catch
            {
                return;
            }
                string msgType = msg.type;
            if (msgType == "LOG")
            {
                string toLog = msg.data.value;
                LogLevel logLevel = msg.data.level;
                ModEntry.Log($"Speech engine message: {toLog}", logLevel);
            }
            //else if (msgType == "UPDATE_HELD_BUTTONS" || msgType == "PRESS_KEY") 
            //{
            //    UpdateTickedRequestQueue.Enqueue(msg);
            //}
            else
            {
                UpdateTickedRequestQueue.Enqueue(msg);
            }
        }

        public void RespondToMessage(dynamic msg, string gameLoopContext) 
        {   
            dynamic resp;
            bool unvalidatedGameContext = gameLoopContext == "UnvalidatedUpdateTicked";
            try
            {
                string msgType = msg.type;
                if (unvalidatedGameContext && !UnvalidatedModeAllowableMessageTypes.Contains(msgType))
                {
                    throw new InvalidOperationException($"Unsafe message type during unvalidated game context: {msgType}");
                }
                dynamic msgData = msg.data;
                resp = Requests.HandleRequest(msg);
            }
            catch (Exception e)
            {
                string body = e.ToString();
                string error = "STACK_TRACE";
                resp = new { body, error };
            }
            string msgId = msg.id;
            this.SendResponse(msgId, resp.body, resp.error);
        }

         

        void onError(string data)
        {
            ModEntry.Log($"Speech engine error: {data}", LogLevel.Debug);
        }

        void SendResponse(string id, object value = null, object error = null) 
        {
            //var respData = new ResponseData(id, value);
            var respData = new { id, value, error };
            this.SendMessage("RESPONSE", respData);
        }

        public bool SendMessage(string msgType, object data = null)     
        {
            if (!this.Running) return false;
            var message = new MessageToEngine(msgType, data);
            var settings = new JsonSerializerSettings() { ReferenceLoopHandling = ReferenceLoopHandling.Ignore };
            settings.Error = (serializer, err) => err.ErrorContext.Handled = true;
            string msgStr = JsonConvert.SerializeObject(message, Formatting.None, settings);
            lock (this.StandardInLock) 
            {
                try
                {
                    this.Proc.StandardInput.WriteLine(msgStr);
                }
                catch (System.InvalidOperationException e) 
                {
                    this.Running = false;
                }
            }
            return true;
        }

        public void SendEvent(string eventType, object data = null) {
            var msg = new { eventType, data };
            this.SendMessage("EVENT", msg);
        }
    }
    class MessageToEngine 
    {
        public string type;
        public object data;
        public MessageToEngine(string type, object data) 
        {
            this.type = type;
            this.data = data;
        }
    }
    class ResponseData
    {
        public string id;
        public object value;
        public ResponseData(string id, object value)
        {
            this.id = id;
            this.value = value;
        }
    }
}
