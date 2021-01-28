using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
using Microsoft.Xna.Framework;
using Newtonsoft.Json;
using StardewSpeak.Pathfinder;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewModdingAPI.Utilities;
using StardewValley;
using StardewValley.Buildings;
using StardewValley.Tools;

namespace StardewSpeak
{
    /// <summary>The mod entry point.</summary>
    public class ModEntry : Mod
    {
        internal static bool FeedLocation = false;
        SpeechEngine speechEngine;
        public static Action<string, LogLevel> log { get; private set; }
        public static Dictionary<string, Stream> Streams { get; set; } = new Dictionary<string, Stream>();

        /*********
** Public methods
*********/
        /// <summary>The mod entry point, called after the mod is first loaded.</summary>
        /// <param name="helper">Provides simplified APIs for writing mods.</param>
        public override void Entry(IModHelper helper)
        {
            helper.Events.Input.ButtonPressed += this.OnButtonPressed;
            helper.Events.GameLoop.UpdateTicked += GameLoop_UpdateTicked;
            helper.Events.Player.Warped += this.OnWarped;
            helper.Events.World.TerrainFeatureListChanged += this.OnTerrainFeatureListChanged;
            helper.Events.World.ObjectListChanged += this.OnObjectListChanged;
            ModEntry.log = this.Monitor.Log;
            this.speechEngine = new SpeechEngine();
            this.speechEngine.LaunchProcess();

        }

        public static void Log(string msg) {
            ModEntry.log(msg, LogLevel.Debug);
        }

        private void OnWarped(object sender, WarpedEventArgs e)
        {
            long milliseconds = DateTime.Now.Ticks / TimeSpan.TicksPerMillisecond;
            var oldLocation = e.OldLocation.NameOrUniqueName;
            var newLocation = e.NewLocation.NameOrUniqueName;
            var warpEvent = new { timestamp = milliseconds, oldLocation, newLocation };
            foreach (var pair in ModEntry.Streams)
            {
                var id = pair.Key;
                var stream = pair.Value;
                if (stream.Name == "ON_WARPED") {
                    var message = new { stream_id = id, value = warpEvent };
                    this.speechEngine.SendMessage("STREAM_MESSAGE", message);
                    Log($"Warped to {e.NewLocation}");
                }
            }
            //this.speechEngine.SendEvent("ON_WARPED", warpEvent);
        }

        private void MessageStreams(string streamName, dynamic messageValue) 
        {
            var messages = Stream.MessageStreams(ModEntry.Streams, streamName, messageValue);
            foreach(var message in messages) 
            {
                this.speechEngine.SendMessage("STREAM_MESSAGE", message);
            }
        }

        private void OnTerrainFeatureListChanged(object sender, TerrainFeatureListChangedEventArgs e)

        {
            var removed = e.Removed.Select(x => new { x.Value.currentTileLocation });
            var changedEvent = new { location = e.Location.NameOrUniqueName, removed };
            this.MessageStreams("ON_TERRAIN_FEATURE_LIST_CHANGED", changedEvent);
            Log($"ON_TERRAIN_FEATURE_LIST_CHANGED");
            //this.speechEngine.SendEvent("ON_WARPED", warpEvent);
        }


        private void OnObjectListChanged(object sender, ObjectListChangedEventArgs e)

        {
            var changedEvent = new { location = e.Location.NameOrUniqueName };
            this.MessageStreams("ON_OBJECT_LIST_CHANGED", changedEvent);
            Log($"ON_OBJECT_LIST_CHANGED");
            //this.speechEngine.SendEvent("ON_WARPED", warpEvent);
        }
        /*********
        ** Private methods
        *********/
        /// <summary>Raised after the player presses a button on the keyboard, controller, or mouse.</summary>
        /// <param name="sender">The event sender.</param>
        /// <param name="e">The event data.</param>
        private void OnButtonPressed(object sender, ButtonPressedEventArgs e)
        {
            // ignore if player hasn't loaded a save yet
            if (!Context.IsWorldReady) { }
                //return;
            // print button presses to the console window
            string pressed = e.Button.ToString();
            //this.Monitor.Log($"{Game1.player.Name} presseddd {e.Button}.", LogLevel.Debug);
            //this.Monitor.Log(e.Button.ToString(), LogLevel.Debug);
            if (pressed == "R") {
                var menu = Game1.activeClickableMenu;
            }
            if (pressed == "P")
            {
                this.Monitor.Log("pressed p");
                if (Routing.Ready)
                {
                    var route = Routing.GetRoute("HaleyHouse");
                    var watch = System.Diagnostics.Stopwatch.StartNew();
                    var targetTile = Game1.currentCursorTile;
                    var targetX = (int)targetTile.X;
                    var targetY = (int)targetTile.Y;

                    var path = Pathfinder.Pathfinder.FindPath(Game1.player.currentLocation, Game1.player.getTileX(), Game1.player.getTileY(), targetX, targetY, -1);
                    if (path == null)
                    {
                        ModEntry.Log("No path found");
                    }
                    else { 
                        foreach(var node in path) {
                            ModEntry.Log($"{node.X}, {node.Y}");
                        }
                    }
                    watch.Stop();
                    var elapsedMs = watch.ElapsedMilliseconds;
                    ModEntry.Log($"{elapsedMs}");
                    }
                else
                {
                    Routing.Reset();
                }
                //Core.EquipToolIfOnHotbar("Pickaxe");
            }
            else if (pressed == "L")
            {
                var player = Game1.player;
                var location = player.currentLocation;
                var mouseX = Game1.getMouseX();
                var mouseY = Game1.getMouseY();
                var point = Game1.currentCursorTile;
                var tileX = (int)point.X;
                var tileY = (int)point.Y;
                var vec = new Vector2(tileX, tileY);
                Log($"Current tiles: x: {tileX}, y: {tileY}");
                Log($"Current mouse position: x: {mouseX}, y: {mouseY}");

                var isPassable = Pathfinder.Pathfinder.IsPassable(location, tileX, tileY);
                var isOccupied = location.isTileOccupiedIgnoreFloors(vec);
                Log($"isPassable: {isPassable}");
                Log($"isOccupied: {isOccupied}\n");
                var rec = new xTile.Dimensions.Location(tileX, tileY);
                Utils.WriteJson("debris.json", location.debris.ToList());
                Utils.WriteJson("objects.json", location.Objects.Values.ToList());
                Utils.WriteJson("resourceClumps.json", location.resourceClumps.ToList());
                Utils.WriteJson("currentTool.json", player.CurrentTool);
            }
        }
        private void GameLoop_UpdateTicked(object sender, UpdateTickedEventArgs e)
        {
            foreach (var pair in ModEntry.Streams)
            {
                var id = pair.Key;
                var stream = pair.Value;
                if (stream.Name != "UPDATE_TICKED" || !e.IsMultipleOf((uint)stream.Data.ticks)) continue;
                var value = stream.Gather(e);
                var message = new { stream_id = id, value };
                this.speechEngine.SendMessage("STREAM_MESSAGE", message);
            }
        }
    }
}