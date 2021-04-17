# StardewSpeak

Play Stardew Valley by voice.

## Installation

## Getting Started

## Commands

Commands wrapped in brackets are optional, meaning that `hello [world]` will match either `hello` or `hello world`. Commands wrapped in brackets or parentheses with `|` describes alternatives. Commands wrapped in `<>` refer to a particular set of alternatives: `<direction>` refers to movement directions, `<n>`, `<x>`, and `<y>` refer to numbers, `<location>` refers to game locations, and `<item>` refers to game items.

See the [menus file](menus.md) for a list of available menu-specific commands.

### General
<table>
    <tr>
        <th>Command</th>
        <th>Description</th>
        <th>Example(s)</th>
    </tr>
    <tr>
        <td>&lt;direction&gt;</td>
        <td>Begin moving in a specific direction. Options are north (up), east (right), south (down), west (left), main (up and right), floor (down and right), air (down and left), and wash (up and left). Using a mnemonic with USA states: Maine in the northeast, Florida in the southeast, Arizona in the southwest and Washington in the northwest.</td>
        <td>"north"</td>
    </tr>
    <tr>
        <td>&lt;n&gt; &lt;direction&gt;</td>
        <td>Move <i>n</i> tiles in a direction and stop. Will pathfind around obstacles as long as the target tile is clear.</td>
        <td>"one two west" - move left 12 tiles</td>
    </tr>
    <tr>
        <td>clear debris</td>
        <td>Begin clearing weeds, stone, and wood.</td>
        <td>"clear debris"</td>
    </tr>
    <tr>
        <td>chop trees</td>
        <td>Begin chopping down nearby trees.</td>
        <td>"chop trees"</td>
    </tr>
    <tr>
        <td>go to &lt;location&gt;</td>
        <td>Walk towards a game <a href="./StardewSpeak/lib/speech-client/speech-client/locations.py">location</a>.</td>
        <td>"go to mines"</td>
    </tr>
    <tr>
        <td>(dig | hoe) &lt;x&gt; by &lt;y&gt;</td>
        <td>Use hoe to dig an <i>x</i> by <i>y</i> grid based on the last two directions faced.</td>
        <td>"dig three by four"</td>
    </tr>
    <tr>
        <td>start planting</td>
        <td>Start planting equipped seeds or fertilizer on available hoe dirt.</td>
        <td>"start planting"</td>
    </tr>
    <tr>
        <td>water crops</td>
        <td>Start watering nearby crops.</td>
        <td>"water crops"</td>
    </tr>
    <tr>
        <td>harvest crops</td>
        <td>Start harvesting fully grown crops.</td>
        <td>"start harvesting"</td>
    </tr>
    <tr>
        <td>pet animals</td>
        <td>Attempt to pet all animals in the current location. Will sometimes fail if the animals are clumped together or are in tight areas that make pathfinding difficult.</td>
        <td>"pet animals"</td>
    </tr>
    <tr>
        <td>milk animals</td>
        <td>Attempt to milk all cows and goats in the current location. Will sometimes fail if the animals are clumped together or are in tight areas that make pathfinding difficult.</td>
        <td>"milk animals"</td>
    </tr>
    <tr>
        <td>start fishing</td>
        <td>Cast fishing rod at maximum distance. If the cast is successful, wait for a nibble and begin reeling.</td>
        <td>"start fishing"</td>
    </tr>
    <tr>
        <td>catch fish</td>
        <td>Automatically complete fish catching minigame. Will also catch any treasure chests that appear.</td>
        <td>"catch fish"</td>
    </tr>
    <tr>
        <td>talk to &lt;npc&gt;</td>
        <td>Move to an NPC and press action button. If the player is holding a giftable item this will gift that item to the NPC. Will fail if the NPC is not in the current location.</td>
        <td>"talk to Leah"</td>
    </tr>
    <tr>
        <td>start shopping</td>
        <td>If in a store location (Pierre's General Store, Marnie's house, etc.), move to shopkeeper and press action button.</td>
        <td>"start shopping"</td>
    </tr>
    <tr>
        <td>[open | read] (quests | journal | quest log)</td>
        <td>Open journal</td>
        <td>"read journal"</td>
    </tr>
    <tr>
        <td>go inside</td>
        <td>Go inside the nearest building, including farm buildings.</td>
        <td>"go inside"</td>
    </tr>
    <tr>
        <td>nearest &lt;item&gt;</td>
        <td>Move to nearest <a href="./StardewSpeak/lib/speech-client/speech-client/items.py">item</a> by name in current location.</td>
        <td>
            <div>"nearest chest"</div>
            <div>"nearest bee house"</div>
        </td>
    </tr>
    <tr>
        <td>(action | check)</td>
        <td>Press action button (default x)</td>
        <td>"action"</td>
    </tr>
    <tr>
        <td>swing</td>
        <td>Use tool (default c)</td>
        <td>"swing"</td>
    </tr>
    <tr>
        <td>stop</td>
        <td>Stop current actions</td>
        <td>"stop"</td>
    </tr>
    <tr>
        <td>item &lt;item&gt;</td>
        <td>Equip the nth item in the toolbar.</td>
        <td>"item seven"</td>
    </tr>
    <tr>
        <td>equip &lt;tool&gt;</td>
        <td>Equip tool if in inventory.</td>
        <td>
            <div>"equip pickaxe"</div>
            <div>"equip shears"</div>
        </td>
    </tr>
    <tr>
        <td>equip [melee] weapon</td>
        <td>Equip melee weapon if in inventory.</td>
        <td>"equip weapon"</td>
    </tr>
    <tr>
        <td>(next | cycle) toolbar</td>
        <td>Cycle the toolbar.</td>
        <td>"next toolbar"</td>
    </tr>
    <tr>
        <td>[left] click [&lt;n&gt;]</td>
        <td>Left click <i>n</i> times.</td>
        <td>"click"</td>
    </tr>
    <tr>
        <td>right click [&lt;n&gt;]</td>
        <td>Right click <i>n</i> times.</td>
        <td>"right click"</td>
    </tr>
    <tr>
        <td>mouse &lt;direction&gt; [&lt;n&gt;]</td>
        <td>Move the mouse <i>n</i> tiles (64 pixels).</td>
        <td>"mouse down"</td>
    </tr>
    <tr>
        <td>small mouse &lt;direction&gt; [&lt;n&gt;]</td>
        <td>Move the mouse <i>n</i> pixels.</td>
        <td>"small mouse down seven"</td>
    </tr>
</table>
