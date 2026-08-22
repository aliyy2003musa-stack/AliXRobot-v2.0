"""
AliXRobot v2.0 - User Guide Content
====================================

Rich HTML documentation shown inside UserGuideDialog (QTextBrowser)
and exported to PDF via QTextDocument/QPrinter.

This module contains ONLY the HTML string — no PyQt6 code, no
application logic. main_page.py imports USER_GUIDE_HTML and nothing
else from here.
"""

USER_GUIDE_HTML = """
<style>
    /* =================================================
       GLOBAL — dark theme throughout
       ================================================= */
    body {
        font-family: 'Segoe UI', Arial, sans-serif;
        background-color: #000000;
        color: #E2E8F0;
        line-height: 1.65;
        font-size: 14px;
        margin: 0;
        padding: 24px;
    }

    a { color: #60A5FA; }

    h1 {
        color: #FFFFFF;
        background-color: #0F172A;
        border: 1px solid #1E293B;
        border-left: 5px solid #3B82F6;
        border-radius: 6px;
        padding: 16px 20px;
        margin: 0 0 20px 0;
        font-size: 24px;
    }
    h2 {
        color: #FFFFFF;
        margin-top: 34px;
        border-left: 5px solid #3B82F6;
        background-color: #0F172A;
        padding: 10px 15px;
        border-radius: 4px;
        font-size: 18px;
    }
    h3 {
        color: #93C5FD;
        margin-top: 22px;
        font-size: 15px;
        font-weight: bold;
    }
    p { color: #CBD5E1; }
    ul, ol { margin-bottom: 15px; padding-left: 24px; color: #CBD5E1; }
    li { margin-bottom: 7px; }
    hr { border: none; border-top: 1px solid #1E293B; margin: 30px 0; }

    /* =================================================
       UTILITY
       ================================================= */
    .highlight {
        background-color: #111827;
        border: 1px solid #1F2937;
        padding: 2px 7px;
        border-radius: 4px;
        font-family: 'Consolas', monospace;
        color: #F59E0B;
        font-weight: bold;
        font-size: 13px;
    }
    .btn {
        background-color: #1E293B;
        color: #E2E8F0;
        padding: 3px 10px;
        border-radius: 4px;
        font-weight: bold;
        border: 1px solid #334155;
        font-size: 13px;
    }
    .kbd {
        background-color: #0F172A;
        border: 1px solid #334155;
        border-bottom: 2px solid #334155;
        border-radius: 4px;
        padding: 1px 7px;
        font-family: 'Consolas', monospace;
        font-size: 12px;
        color: #FBBF24;
    }

    /* =================================================
       CALLOUT BOXES — dark variants
       ================================================= */
    .note {
        background-color: #0B1D33;
        border-left: 4px solid #3B82F6;
        padding: 12px 16px;
        margin: 15px 0;
        border-radius: 4px;
        color: #DBEAFE;
    }
    .warning {
        background-color: #2A0F0F;
        border-left: 4px solid #EF4444;
        padding: 12px 16px;
        margin: 15px 0;
        border-radius: 4px;
        color: #FECACA;
    }
    .tip {
        background-color: #0B2116;
        border-left: 4px solid #22C55E;
        padding: 12px 16px;
        margin: 15px 0;
        border-radius: 4px;
        color: #BBF7D0;
    }

    /* =================================================
       MATRIX / CODE BLOCKS
       ================================================= */
    .matrix-box {
        background-color: #05070C;
        border: 1px solid #1F2937;
        color: #34D399;
        padding: 16px;
        border-radius: 6px;
        font-family: 'Consolas', monospace;
        font-size: 13px;
        margin: 10px 0;
        white-space: pre;
        overflow-x: auto;
    }

    /* =================================================
       TABLE OF CONTENTS
       ================================================= */
    .toc {
        background-color: #0F172A;
        border: 1px solid #1E293B;
        border-radius: 6px;
        padding: 16px 20px;
        margin-bottom: 26px;
    }
    .toc h3 { margin-top: 0; color: #60A5FA; }
    .toc ul { list-style-type: none; padding-left: 0; margin-bottom: 0; }
    .toc li { margin-bottom: 6px; }
    .toc a { text-decoration: none; color: #E2E8F0; font-weight: 500; }
    .toc a:hover { color: #60A5FA; text-decoration: underline; }

    /* =================================================
       DATA TABLE
       ================================================= */
    table.compare {
        width: 100%;
        border-collapse: collapse;
        margin: 12px 0 20px 0;
        font-size: 13px;
    }
    table.compare th {
        background-color: #1E293B;
        color: #FFFFFF;
        text-align: left;
        padding: 8px 10px;
        border: 1px solid #334155;
    }
    table.compare td {
        background-color: #0B1220;
        color: #CBD5E1;
        padding: 8px 10px;
        border: 1px solid #1E293B;
    }
</style>

<h1>AliXRobot v2.0 &mdash; User Guide</h1>
<p>AliXRobot is a robotics transformation and kinematics visualization tool built to
support robotics research, education, and simulation work. This guide covers the 2D/3D
math engine, the vertex table, the 3D and Animation viewers, the interpolation profiles,
and both export systems &mdash; so you always know exactly where a feature lives and
what it does.</p>

<div class="toc">
    <h3>Quick Navigation</h3>
    <ul>
        <li><a href="#sec1">1. 2D vs 3D &mdash; What Each Mode Actually Does</a></li>
        <li><a href="#sec2">2. The 3D Viewer &mdash; Isometric View &amp; Mouse Rotation</a></li>
        <li><a href="#sec3">3. Building a Robot (Parameters &amp; the Vertex Table)</a></li>
        <li><a href="#sec4">4. The "Calculate TRS" Shortcut</a></li>
        <li><a href="#sec5">5. The Animation Studio</a></li>
        <li><a href="#sec6">6. Motion Profiles Explained</a></li>
        <li><a href="#sec7">7. View Toggles: Traj, Ghosts, Frames</a></li>
        <li><a href="#sec8">8. Reading the Telemetry Graph</a></li>
        <li><a href="#sec9">9. Exporting Your Work (Two Separate Systems)</a></li>
        <li><a href="#sec10">10. Troubleshooting</a></li>
        <li><a href="#sec11">11. Contact &amp; Support</a></li>
    </ul>
</div>

<h2 id="sec1">1. 2D vs 3D &mdash; What Each Mode Actually Does</h2>
<p>Switching between <span class="highlight">2D</span> and <span class="highlight">3D</span>
changes the size of the transformation matrix the engine builds behind the scenes, and
changes what shape your vertex data needs to be in.</p>

<h3>2D Mode &mdash; 3&times;3 Homogeneous Matrix</h3>
<div class="matrix-box">[ cos&theta;  -sin&theta;   Tx ]   [ x ]   [ x' ]
[ sin&theta;   cos&theta;   Ty ] &times; [ y ] = [ y' ]
[   0       0      1  ]   [ 1 ]   [ 1  ]</div>
<p>Only X and Y are tracked. Vertices must be entered as <span class="highlight">[x, y]</span>
pairs. Rotation always happens around the implicit Z axis (there's no axis choice in 2D).</p>

<h3>3D Mode &mdash; 4&times;4 Homogeneous Matrix</h3>
<div class="matrix-box">[ r11  r12  r13  Tx ]   [ x ]   [ x' ]
[ r21  r22  r23  Ty ] &times; [ y ] = [ y' ]
[ r31  r32  r33  Tz ]   [ z ]   [ z' ]
[  0    0    0   1  ]   [ 1 ]   [ 1  ]</div>
<p>X, Y, and Z are all tracked, and you choose a rotation axis (x, y, or z). Vertices must
be entered as <span class="highlight">[x, y, z]</span> triples.</p>

<div class="warning">
    <b>Dimension mismatch:</b> if you build a robot in 3D, then flip to 2D without clearing
    the table, your vertex row count no longer matches what 2D expects (3 rows vs 2).
    Click <span class="btn">Clear Transformations</span> before switching dimensions.
</div>

<h2 id="sec2">2. The 3D Viewer &mdash; Isometric View &amp; Mouse Rotation</h2>
<p>Open the <span class="btn">3D View</span> tab under Graphical Representation. The
scene is drawn as an <b>isometric projection</b> &mdash; a fixed-angle 2D drawing that
represents 3D space without needing a full 3D graphics engine.</p>
<ul>
    <li><b>Click and drag</b> anywhere on the canvas to rotate the camera around the scene.</li>
    <li>The small axis triad at the origin (red X, green Y, blue Z) always shows you the
    current orientation as you rotate.</li>
    <li>The <span style="color:#F87171">red</span> marker is the <b>Original</b> point,
    the <span style="color:#60A5FA">blue</span> marker is the <b>Transformed</b> point,
    connected by a dashed line showing the transformation path.</li>
</ul>
<div class="tip">
    <b>Tip:</b> rotate the camera to a top-down angle when checking pure X/Y motion, or to
    a side angle when checking Z-axis (height) changes &mdash; the isometric default view
    can visually flatten motion along a single axis.
</div>

<h2 id="sec3">3. Building a Robot (Parameters &amp; the Vertex Table)</h2>
<p>The <b>Robot Parameters</b> panel on the left is where every robot starts.</p>
<h3>Two ways to enter vertices &mdash; they stay in sync</h3>
<ul>
    <li><b>The table:</b> rows are axes (X, Y[, Z]), columns are vertices (V1, V2, &hellip;).
    Type numbers directly into cells. Change <span class="highlight">Number of vertices</span>
    to add/remove columns.</li>
    <li><b>The "Initial position" box:</b> type a bracketed list instead &mdash;
    <span class="highlight">[2, 3, 4]</span> for one vertex, or
    <span class="highlight">[[2,3,4],[4,3,6]]</span> for several. Press Enter and the table
    fills in automatically. Editing the table also updates this box in the other direction.</li>
</ul>
<div class="warning">
    <b>Missing brackets:</b> typing <span class="highlight">2, 3, 4</span> without the
    outer <span class="highlight">[ ]</span> will be rejected. The parser needs a proper
    Python-style list.
</div>
<h3>Other fields</h3>
<p><b>Robot type</b> and <b>Degrees of freedom</b> are descriptive/record-keeping fields
carried through to your exports. <b>Velocity, Acceleration, Inertia matrix, PID gains</b>
are optional metadata fields also carried into your exports &mdash; they don't affect the
transformation math itself.</p>

<div class="tip">
    <b>Scales to N vertices:</b> the table and Initial position box aren't limited to a
    handful of points &mdash; the same matrix math handles complex shapes with dozens or
    hundreds of vertices just as reliably. For example, a 150-vertex curve like:
    <div class="matrix-box">[
    [0.0, 0.0], [0.5, 0.4], [1.0, 0.9], [1.5, 1.5], [2.0, 2.2],
    [2.5, 2.9], [3.0, 3.5], [3.5, 4.0], [4.0, 4.4], [4.5, 4.7],
    ...
    [69.0, 2.2], [69.5, 2.7], [70.0, 3.0],
]  &larr; 150 vertices total</div>
    transforms, animates, and exports exactly the same way a 3-vertex triangle does &mdash;
    just paste the full list into the Initial position box and press Enter.
</div>

<h2 id="sec4">4. The "Calculate TRS" Shortcut</h2>
<p><span class="btn">Calculate Transformation Combination (TRS)</span> lets you try a new
Translation/Rotation/Scaling combo on your <i>already-entered</i> vertices without retyping
them.</p>
<ol>
    <li>Enter your vertices once (table or Initial position box).</li>
    <li>Check the boxes for the operations you want: Translation, Rotation, Scaling.</li>
    <li>Click <span class="btn">Calculate TRS</span> &mdash; a dialog pops up for each
    checked operation's values.</li>
    <li>The graph and Robot Information panel update immediately.</li>
</ol>
<div class="tip">
    <b>Tip:</b> click TRS again with different values to rapidly test several rotation
    angles or scale factors on the same shape &mdash; no need to click Define Robot each time.
</div>
<div class="warning">
    <b>Nothing happens?</b> TRS needs at least one checkbox ticked. With none checked, there's
    no operation for it to calculate.
</div>

<h2 id="sec5">5. The Animation Studio</h2>
<p>Open the <span class="btn">Animation</span> tab to interpolate your robot smoothly from
its Original position to its Transformed position.</p>
<h3>Primary controls (always visible)</h3>
<p><span class="btn">Play</span> <span class="btn">Pause</span> <span class="btn">Stop</span>
<span class="btn">Loop</span> &mdash; standard transport. Next to them: the
<b>Profile</b> and <b>Speed</b> dropdowns (see section 6), and the
<span class="btn">More Controls</span> toggle on the far right.</p>
<h3>Behind "More Controls"</h3>
<p>Click it to reveal <b>Render</b> mode (Solid / Wireframe / Simple &mdash; visual style
only), the <span class="btn">Traj</span> / <span class="btn">Ghosts</span> /
<span class="btn">Frames</span> view toggles (section 7), and the animation's own
<span class="btn">CSV</span> / <span class="btn">PDF</span> telemetry export (section 9).</p>
<h3>Timeline scrubber</h3>
<p>Drag the slider above the control bar to jump to any point (0&ndash;100%) in the
interpolation and inspect that exact pose &mdash; independent of Play/Pause.</p>
<h3>Keyboard shortcuts</h3>
<p>With the animation canvas focused: <span class="kbd">Space</span> play/pause,
<span class="kbd">Esc</span> stop, <span class="kbd">&larr;</span> / <span class="kbd">&rarr;</span>
scrub backward/forward.</p>

<h2 id="sec6">6. Motion Profiles Explained</h2>
<p>The <b>Profile</b> dropdown controls the timing curve of the interpolation &mdash; it
changes <i>how</i> the robot moves between start and end, not <i>where</i> it ends up.</p>
<ul>
    <li><b>Linear:</b> constant speed the entire time. Simple, but starts and stops
    instantly &mdash; physically unrealistic (infinite acceleration at the endpoints).</li>
    <li><b>Cubic</b> (and <b>Smoothstep</b>, which is the identical curve under a
    different name): eases in and out smoothly. Continuous velocity, no sudden jerks.</li>
    <li><b>Quintic:</b> an even smoother ease than Cubic &mdash; continuous position,
    velocity, <i>and</i> acceleration. The best choice for anything that needs to look
    genuinely fluid.</li>
    <li><b>S-Curve:</b> a two-phase accelerate-then-decelerate ramp, the same shape
    industrial "trapezoidal" motion profiles use in real robotic arms &mdash; smooth
    enough to protect motors and avoid jerky starts.</li>
</ul>
<div class="note">
    <b>Location:</b> Profile and Speed sit together in the primary control bar, right next
    to the More Controls button &mdash; not hidden behind it.
</div>

<h2 id="sec7">7. View Toggles: Traj, Ghosts, Frames</h2>
<p>Found inside <span class="btn">More Controls</span>. Purely visual &mdash; none of them
change the math.</p>
<ul>
    <li><b>Traj</b> (Trajectory): draws the actual curved path the end-effector travels as
    it animates, as opposed to the straight dashed Original&rarr;Target line, which is
    always shown regardless of this toggle.</li>
    <li><b>Ghosts</b> (Motion history): shows up to 8 fading previous poses behind the
    current one &mdash; a motion-blur effect that helps judge speed and direction at a
    glance.</li>
    <li><b>Frames</b>: draws small X/Y/Z axis crosses at the world origin, the base, and
    the end-effector, so you can see <i>orientation</i>, not just position.</li>
</ul>
<div class="warning">
    <b>Ghosts shows nothing?</b> Motion history only records while the animation is
    actually playing. Turning it on after a run has already finished won't retroactively
    fill in the trail &mdash; press Play again with Ghosts already on.
</div>

<h2 id="sec8">8. Reading the Telemetry Graph</h2>
<p>The dark chart titled <b>Real-Time End-Effector Telemetry</b>, directly under the
animation canvas, plots the end-effector's X (red), Y (green), and Z (blue) coordinates
against animation progress (0&ndash;100%) as it plays.</p>
<div class="tip">
    <b>Why it matters:</b> smooth curves confirm your transformation and interpolation
    profile are behaving correctly. A sudden spike or discontinuity usually means bad
    input values, not a bug &mdash; double-check your Translation/Rotation/Scaling numbers.
</div>

<h2 id="sec9">9. Exporting Your Work (Two Separate Systems)</h2>
<p>AliXRobot has <b>two independent</b> export pairs &mdash; easy to mix up since they're
both labelled CSV/PDF. Here's the difference:</p>
<table class="compare">
    <tr><th>Location</th><th>Buttons</th><th>What it exports</th></tr>
    <tr>
        <td>Robot Information panel (right side, always visible)</td>
        <td>Export PDF Report / Export CSV Data</td>
        <td>Your robot's <b>configuration</b>: dimension, type, DOF, every vertex
        (original &amp; transformed), and the full transformation matrix &mdash; a
        one-shot snapshot.</td>
    </tr>
    <tr>
        <td>Animation tab &rarr; More Controls</td>
        <td>CSV / PDF</td>
        <td><b>Time-series telemetry</b> recorded frame-by-frame while the animation
        plays: progress %, X/Y/Z at each sampled instant. Requires running the animation
        at least once first.</td>
    </tr>
</table>
<div class="note">
    Use the Robot Information exports for a snapshot of your setup; use the Animation
    exports when you need to show <i>how</i> the motion evolved over time.
</div>

<h2 id="sec10">10. Troubleshooting</h2>
<h3>"My robot disappeared from the view!"</h3>
<p><b>Cause:</b> a Scaling factor of 0, or a Translation that moved it far outside the
visible range.<br><b>Fix:</b> click <span class="btn">Reset View</span> on the 2D/3D tab,
or re-check your Scaling/Translation values.</p>

<h3>"The animation looks jerky."</h3>
<p><b>Cause:</b> you're on the <b>Linear</b> profile, which has instant start/stop.<br>
<b>Fix:</b> switch to <b>Quintic</b> or <b>S-Curve</b> in the Profile dropdown.</p>

<h3>"Vertex parsing failed / dimension error."</h3>
<p><b>Cause:</b> you entered 3D-shaped vertices <span class="highlight">[[x,y,z]]</span>
while in 2D mode, or vice versa.<br><b>Fix:</b> match your vertex bracket count to the
selected dimension, or clear and re-enter after switching.</p>

<h3>"Ghosts / Traj toggle doesn't seem to do anything."</h3>
<p><b>Cause:</b> Traj and Frames update immediately since they render data that's already
there; Ghosts specifically needs the animation actively playing <i>after</i> you enable it
to start recording history &mdash; see section 7.</p>

<h2 id="sec11">11. Contact &amp; Support</h2>
<p>AliXRobot v2.0 is designed to support robotics research, education, and simulation
work &mdash; covering homogeneous transformations, geometric transformations, and
kinematics. Stay tuned for future upgrades, including inverse kinematics and dynamic
simulation.</p>
<div class="note">
    <b>Get in touch:</b> for bug reports, feature requests, technical advice, or
    collaboration on this project, reach the development team directly:
    <ul>
        <li>Email: <span class="highlight">aliyy23musa@gmail.com</span></li>
        <li>Linkedin: <span class="highlight">https://www.linkedin.com/in/aliyy-gbolahan</span></li>
    </ul>
</div>
"""