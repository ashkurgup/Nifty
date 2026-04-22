<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Market Dashboard</title>
    <link rel="stylesheet" href="style.css">
    <link href="https://fonts.googleapis.com/css2?family=Lato:wght@400;700;900&display=swap" rel="stylesheet">
</head>
<body>

<div class="dashboard-line" style="display: flex; gap: 10px; align-items: stretch; width: 100%;">

    <div class="box box-nifty" style="flex: 0 0 210px; padding: 15px; min-height: 160px;">
        <div style="display: flex; flex-direction: column; height: 100%; justify-content: space-between;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 16px; font-weight: 900; color: #111827;">NIFTY</span>
                <span id="marketStatus" style="font-size: 10px; font-weight: 800; letter-spacing: 0.5px;">● --</span>
            </div>
            <div style="margin: 10px 0;">
                <div id="niftyPrice" style="font-size: 28px; font-weight: 900; color: #111827; line-height: 1;">--</div>
                <div id="niftyChange" style="font-size: 13px; font-weight: 700; margin-top: 4px;">--</div>
            </div>
            <hr style="border: 0; border-top: 1px solid #f1f5f9; margin: 5px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-size: 8px; color: #9ca3af; font-weight: 800; text-transform: uppercase;">Low</div>
                    <div id="niftyLow" style="font-size: 11px; font-weight: 700; color: #374151;">--</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 8px; color: #9ca3af; font-weight: 800; text-transform: uppercase;">High</div>
                    <div id="niftyHigh" style="font-size: 11px; font-weight: 700; color: #374151;">--</div>
                </div>
            </div>
            <div id="niftyUpdated" style="font-size: 10px; margin-top: 8px;">--</div>
        </div>
    </div>

    <div class="center-rows" style="flex: 1; display: flex; flex-direction: column; gap: 8px;">
        
        <div class="box" style="padding: 12px; display: flex; align-items: center;">
            <div class="bias-line" style="font-size: 14px;">
                Structural Bias → 4H <span id="bias4H" class="sq"></span> / 1H <span id="bias1H" class="sq"></span> / 15M <span id="bias15M" class="sq"></span> → <span id="biasMessage" style="font-weight:700;">--</span>
            </div>
        </div>

        <div class="box" style="padding: 10px;">
            <div style="display: flex; align-items: center; gap: 12px; width: 100%;">
                <div class="meter"><div id="globalMeterFill" class="meter-fill"></div></div> 
                <span id="globalMeterValue" style="font-weight: 800; min-width: 25px;">--</span>
                <span style="color: #e5e7eb;">|</span>
                <div id="globalMarkets" style="display: flex; align-items: center; flex-grow: 1; overflow: hidden;"></div>
            </div>
        </div>

        <div class="box" style="padding: 10px;">
            <div style="display: flex; align-items: center; gap: 12px; width: 100%;">
                <div class="meter"><div id="breadthFill" class="meter-fill"></div></div> 
                <span id="breadthMeterValue" style="font-weight: 800; min-width: 25px;">--</span>
                <span style="color: #e5e7eb;">|</span>
                <div id="breadthSectors" style="display: flex; align-items: center; flex-grow: 1; overflow: hidden;"></div>
            </div>
        </div>
    </div>

    <div style="flex: 0 0 200px; display: flex; flex-direction: column; gap: 8px;">
        <div class="box box-side" style="height: 50%;">
            <div class="side-title">STRATEGY</div>
            <div class="side-val" style="font-size: 18px; font-weight: 900; margin: 4px 0;">Active</div>
            <div id="stratLevels" style="font-size: 11px; font-weight: 700;">SMC Protocol</div>
        </div>
        <div class="box box-side" style="height: 50%;">
            <div class="side-title">WEALTH 2029</div>
            <div id="wealthVal" style="font-size: 18px; font-weight: 900; margin: 4px 0;">--%</div>
            <div class="small">Debt-Free Goal</div>
        </div>
    </div>

</div>

<hr class="faint-divider">

<div class="secondary-row" style="display: flex; gap: 10px;">
    <div class="box" style="flex: 1; text-align: center;">Metric 1</div>
    <div class="box" style="flex: 1; text-align: center;">Metric 2</div>
    <div class="box" style="flex: 1; text-align: center;">Metric 3</div>
    <div class="box" style="flex: 1; text-align: center;">Metric 4</div>
    <div class="box" style="flex: 1; text-align: center;">Metric 5</div>
</div>

<hr class="faint-divider">

<div class="third-row">
    <div class="box" style="padding: 15px; font-weight: 800;">Market Overview & Deep Analytics</div>
</div>

<hr class="faint-divider">

<script src="app.js"></script>
</body>
</html>
