<?php

session_start();

function clearHistory($limit)
{
  $workFolder = "workspace/";
  
  if ($handle = opendir($workFolder))
  {
    $batchFolders = array();
    {
      $dir = new DirectoryIterator($workFolder);
   
      foreach ($dir as $fileinfo)
      {
        if ($fileinfo->getFilename() == "." || $fileinfo->getFilename() == "..")
          continue;
        
        $batchFolders[$fileinfo->getMTime()] = $fileinfo->getFilename();
      }

      krsort($batchFolders);
    }
    
    $index = 0;
    
    foreach ($batchFolders as $folder)
    {
      $index++;
      
      if ($index >= $limit)
      {
        $fullPath = $workFolder.$folder;
        exec("rm -rf ".$fullPath."/*.zip");
        exec("rm -rf ".$fullPath."/output");
        exec("rm -rf ".$fullPath."/output_p");
        exec("rm -rf ".$fullPath."/output_s");
      }
    }
  }
}

function preProcess()
{
  clearHistory(50);
  
  if (empty($_FILES["file"]["name"]) || !is_uploaded_file($_FILES["file"]["tmp_name"]))
  {
    echo "ERROR,ERROR: It doesn't look like you have uploaded a valid file. Please go back and do it again.";
    return;
  }
  
  $username = "guest";
  $password = "";
  
  if ($_POST["username"] != null || $_POST["password"] != null)
  {
    $username = $_POST["username"];
    $password = $_POST["password"];
  }
    
  //prepare a workfolder
  $id = date("Ymd")."_".mt_rand();
  
  $workFolder = "workspace/".$id."/";
  exec("mkdir ".$workFolder);
  
  move_uploaded_file($_FILES["file"]["tmp_name"], $workFolder.$_FILES["file"]["name"]);
   
  $_SESSION['id'] = $id;
  $_SESSION['csvFile'] = $workFolder.$_FILES["file"]["name"];
  $_SESSION['username'] = $username;
  $_SESSION['password'] = $password;
  
  echo $id;
}

?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- The above 3 meta tags *must* come first in the head; any other head content must come *after* these tags -->
    <meta name="description" content="">
    <meta name="author" content="">
    <link rel="icon" href="../../favicon.ico">

    <title>Aperio Image ROI Extraction - IVG - ABCC - DSITP - Leidos Biomed</title>

    <!-- Bootstrap core CSS -->
    <link href="bootstrap/css/bootstrap.css" rel="stylesheet">

    <!-- Custom styles -->
    <link href="bootstrap/css/sticky-footer-navbar.css" rel="stylesheet">
    <link rel="stylesheet" href="css/blueimp-gallery.min.css">
    <link rel="stylesheet" href="css/bootstrap-image-gallery.min.css">
    <!-- Bootstrap core JavaScript
    ================================================== -->
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
    <script src="bootstrap/js/bootstrap.js"></script>
    <script src="js/jquery.blueimp-gallery.min.js"></script>
    <script src="js/bootstrap-image-gallery.min.js"></script>
    <!-- IE10 viewport hack for Surface/desktop Windows 8 bug -->
    <script src="bootstrap/js/ie10-viewport-bug-workaround.js"></script>
    <script type="text/javascript" src="d3/d3.js"></script>
    <!-- HTML5 shim and Respond.js for IE8 support of HTML5 elements and media queries -->
    <!--[if lt IE 9]>
    <script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
    <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
    <![endif]-->
    <style>
        #links img {
            border: 1px solid #008cba;
            margin: 3px;
        }
        .page-header {
            margin-top: 20px;
        }
    </style>
</head>

<body>
<!-- The Bootstrap Image Gallery lightbox -->
<div id="blueimp-gallery" class="blueimp-gallery">
    <!-- The container for the modal slides -->
    <div class="slides"></div>
    <!-- Controls for the borderless lightbox -->
    <h3 class="title"></h3>
    <a class="prev">‹</a>
    <a class="next">›</a>
    <a class="close">×</a>
    <a class="play-pause"></a>
    <ol class="indicator"></ol>
    <!-- The modal dialog, which will be used to wrap the lightbox content -->
    <div class="modal fade">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" aria-hidden="true">&times;</button>
                    <h4 class="modal-title"></h4>
                </div>
                <div class="modal-body next"></div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-default pull-left prev">
                        <i class="glyphicon glyphicon-chevron-left"></i>
                        Previous
                    </button>
                    <button type="button" class="btn btn-primary next">
                        Next
                        <i class="glyphicon glyphicon-chevron-right"></i>
                    </button>
                </div>
            </div>
        </div>
    </div>
</div>
<!-- Fixed navbar -->
<nav class="navbar navbar-inverse navbar-fixed-top">
    <div class="container">
        <div class="navbar-header">
            <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#navbar" aria-expanded="false" aria-controls="navbar">
                <span class="sr-only">Toggle navigation</span>
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
            </button>
            <a class="navbar-brand" href="index.html">Aperio Image ROI Extraction Workflow</a>
        </div>
        <div id="navbar" class="collapse navbar-collapse">
            <ul class="nav navbar-nav">
                <li class="active"><a href="index.html">Home</a></li>
                <li class="dropdown">
                    <a href="#" class="dropdown-toggle" data-toggle="dropdown" role="button" aria-haspopup="true" aria-expanded="false">Actions <span class="caret"></span></a>
                    <ul class="dropdown-menu">
                        <li><a href="#" data-toggle="modal" data-target="#workflowOne">Workflow One</a></li>
                        <li><a href="#" data-toggle="modal" data-target="#workflowTwo">Workflow Two</a></li>
                        <li role="separator" class="divider"></li>
                        <li class="dropdown-header">Statistics</li>
                        <li><a href="#" data-toggle="modal" data-target="#stats">View ROI Stats</a></li>
                    </ul>
                </li>
                <li><a href="mailto:miaot2@nih.gov?Subject=Aperio%20Workflow">Contact</a></li>
            </ul>
        </div><!--/.nav-collapse -->
    </div>
</nav>

<!-- Begin page content -->
<div class="container">
    <div class="page-header">
        <h3>ROI Extraction Report</h3>
    </div>
      <div class="row">
          <div class="col-md-12" id="identifier">
              <div id="message"></div>
          </div>
      </div>
      <div class="row"><div class="col-md-12" id="reportTable"></div></div>
      <script type="text/javascript">
        var info = "<?php preProcess();?>";
        var infoArray = info.split(',');
        var id;
        var mytimer;
        
        function getUpdates()
        {
          $.get("workspace/" + id + "/status.txt", function(data){
            
            var lines = data.split("\n");
            var status = '';
            $.each(lines, function(n, elem){
              status += elem + '<br>';
            });
            
            document.getElementById("message").innerHTML = "<p>Please wait while we generate your report.<br />Status: " + status + "</p>";
          });
        }
        
        if (infoArray[0] == "ERROR")
        {
					document.getElementById("identifier").innerHTML = '<div class="col-md-6 alert alert-info"><h5>' + infoArray[1] + '<a href="index.html" class="btn btn-primary btn-small" style="margin-left: 20px;">Try Again</a></h5></div>';
				}
				else
				{
					id = infoArray[0];
          
					$.ajax({
						type: "GET",
						url: "workflow1_backend.php",
						success: function (result){ doReport(result);}
					});
          
          mytimer = setInterval(getUpdates, 2000);
				}
			
				function getTypeString(t)
				{
					if (t == 0)
						return "Image";
					else if (t == 1)
						return "Annotation Layer";
					else
						return "";
				}
						
				function createImageGroup(data)
				{
          var reportArray = [];
          var newReportArray = {};
          data.forEach(function(d, i) {
            newReportArray[d.ImageID] = {};
            
          });

					data.forEach(function(d, i) {
            //console.log(d);
            var imgName = d.ROIFile.slice(0, d.ROIFile.lastIndexOf(".tif"));
            imgName += ".jpg";
            if (newReportArray[d.ImageID][d.LayerName] == "" || newReportArray[d.ImageID][d.LayerName] == null) {
              newReportArray[d.ImageID][d.LayerName] = imgName;
            } else {
              newReportArray[d.ImageID][d.LayerName] += "," + imgName;
            }
					});

          // Build reportArray formatted for function doReport()
          for(var i in newReportArray) {
              for(var j in newReportArray[i]) {
                  var line = new Object;
                  //console.log("ID: " + i);
                  line.id = i;
                  //console.log("Layer: " + j);
                  line.layer = j;
                  //console.log("Images: " + newReportArray[i][j]);
                  line.images = newReportArray[i][j];
                  reportArray.push(line);
              }
          }

          //console.log(newReportArray);
					return reportArray;
				}
						
				function doReport(result)
        {
          clearInterval(mytimer);
          
					var results = result.split(",");
          
          var heading = '<p>Processing complete. Click tabs to navigate between sets. Click on thumbnails to enlarge images.</p>';
          heading += '<table class="table table-striped table-hover "><thead><tr><th>Total Number & Time Taken</th><th>Download Complete Extraction</th><th>Reference ID</th><th>Line Annotations</th></tr></thead>';
          heading += '<tbody><tr class="active"><td>' + results[0] + '</td><td>' + results[1] + '</td><td>' + id + '</td><td>' + results[2] + '</td></tr></tbody></table>';

          document.getElementById("identifier").innerHTML = heading;
					//document.getElementById("identifier").innerHTML = "<h4>" + results[0] + " " + results[1] + "<br>" + results[2] + " (" + id + ")</h4>";
					
					d3.csv("workspace/" + id + "/result.csv", function(error, data){
						
            var reportArray = createImageGroup(data);
            //console.log(reportArray);

            //Start constructing html for tabbed layout
            var setNum = 1;
            var lastImg;
            var imgArray = [];
            var message = '<ul class="nav nav-tabs">';
            
            //Build Tab for each set
            reportArray.forEach(function(d){
            if (d.id !== lastImg) {
              if (setNum == 1) {
                message += '<li class="active"><a href="#' + d.id + '" data-toggle="tab">Set ' + d.id + '</a></li>';
              } else {
                message += '<li><a href="#' + d.id + '" data-toggle="tab">Set ' + d.id + '</a></li>';
              }
            }
            
            lastImg = d.id;
            imgArray[setNum-1] = d.id;
            setNum++;
            });
            
            message += '</ul>';
            //End tabs

            //Main <div> to hold tab content
            message += '<div id="tabContent" class="tab-content">';
            //Build <div> for each set
            setNum = 1;
            lastImg = "";
            var div;
            reportArray.forEach(function(d, i){
              if (d.id !== lastImg) {
                if (setNum == 1) {
                  message += '<div class="tab-pane fade active in" id="' + d.id + '">';
                } else {
                  message += '<div class="tab-pane fade" id="' + d.id + '">';
                }
              }
            
              message += "<table class='table table-striped'><tr><th>Image ID</th><th>Annotation Layer</th><th>Extracted ROIs of Current Set</th><th></th></tr>";

              var imgs = d.images.split(",");

              message += "<tr><td>" + d.id + "</td><td>" + d.layer + "</td><td>" + imgs.length + "</td><td><div class='checkbox' style='margin-top: 0; margin-bottom: 0;'><label><input type='checkbox'> Download this set</label></div></td></tr><tr colspan='6'><td colspan='6'><div id='links'>";

              imgs.forEach(function (o) {
                var linkStr = "<a href='workspace/" + id + "/output_p/" + d.id + "/" + o + "' title='Image ID " + d.id + "' data-gallery data-description='" + o + "'>";
                message += linkStr;
                message += "<img src='" + "workspace/" + id + "/output_s/" + d.id + "/" + o + "'>";
                message += "</a>";
              });

              message += "</div></td></tr>";
              message += "</table>";
            
              if (imgArray[setNum] !== d.id) {
                message += "</div>";
              }
            
              lastImg = d.id;
              setNum++;
            });//reportArray.forEach
              
            message += '</div>';
              
            document.getElementById("reportTable").innerHTML = message;
					});//d3.csv
				}
      </script>
    </div>
    <!-- Sticky Footer -->
    <footer class="footer">
        <div class="container">
            <p class="text-muted">BETA Version - IVG - ABCC - DSITP - Leidos Biomed - <a href="mailto:miaot2@nih.gov?Subject=Aperio%20Workflow" target="_top">Contact: Tianyi Miao @ ABCS.</a></p>
        </div>
    </footer>
  </body>
</html>
