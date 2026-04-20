<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Market Dashboard</title>
  <link rel="stylesheet" href="style.css">
</head>

<body>

<div class="dashboard-row">

  <div class="box box-nifty">
    <div class="nifty-title">NIFTY <span id="dataStatus" class="status"></span></div>
    <div id="niftyPrice" class="nifty-price">--</div>
    <div id="niftyChange" class="nifty-change">--</div>
    <div class="divider"></div>
    <div id="niftyTime" class="small" title="">Updated: --</div>
  </div>

  <div class="right-column">

    <div class="box">
      <div class="bias-line">
        Structural Bias →
        4H <span id="bias4H" class="sq"></span>
        / 1H <span id="bias1H" class="sq"></span>
        / 15M <span id="bias15M" class="sq"></span>
        →
        <span id="biasPhase" class="bias-phase"></span>
      </div>
    </div>

    <div class="box">
      <div class="meter-line">
        <div class="meter">
          <div id="globalMeterFill" class="meter-fill"></div>
        </div>
        <span>Dow <span id="dowVal"></span>%</span>
        <span>DAX <span id="daxVal"></span>%</span>
        <span>Nikkei <span id="nikkeiVal"></span>%</span>
        <span>HSI <span id="hangVal"></span>%</span>
      </div>
    </div>

    <div class="box">
      <div class="meter-line">
        <div class="meter">
          <div id="niftyBreadthFill" class="meter-fill"></div>
        </div>
        BANK | FIN | IT | METAL | FMCG
      </div>
    </div>

  </div>
</div>

<script src="script.js"></script>
</body>
</html>
