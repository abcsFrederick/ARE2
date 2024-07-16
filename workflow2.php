<?php

//echo phpinfo();

function getSafeInputValue($input)
{
  $output = trim(rtrim($input));
  
  if (strlen($output) > 0)
  {
		$targets = array(" ", "/", ":", "?", ">", "\\", "%", "|", "#", "*", ",");
		
		$output = str_replace($targets, "-", $output);
	}
  else
    $output = "-";
  
  return $output;
}

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
        exec("rm -rf ".$fullPath);
      }
    }
  }  
}

function prepareInputs($outputFile, $username, $password, $workFolder)
{
  $indexFile = fopen($outputFile, "w");
  
  if ($indexFile == FALSE)
		return "ERROR,ERROR: Unable to create index file!";
  
  $numRows = 8;
	
	$tissue = getSafeInputValue($_POST["tissue"]);
  $stain = getSafeInputValue($_POST["stain"]);
  
	for ($i = 1; $i <= $numRows; $i++)
  {
    if ($_POST["link".$i] == null)
			continue;
			
		$link = getSafeInputValue($_POST["link".$i]);
    $extID = getSafeInputValue($_POST["extID".$i]);
    
    //-----------parse location-------
    $loc = str_replace("\\", "/", $link);
    
    $subTokens = explode("/", $loc);
    $numSubTokens = count($subTokens);
    
    $archiveBase = "/is1/projects/phl_scanscope/";
    $oldArchive = "archive/PHL/Aperio/";
    $newArchive = "static/";
    
    $loc = $archiveBase;
    
    if (strpos($link, "archive") !== false)
			$loc .= $oldArchive;
		else
			$loc .= $newArchive;
			
		$loc .= $subTokens[$numSubTokens-2]."/".$subTokens[$numSubTokens-1];
		//------------end parse location--------
		
		$imgFile = $subTokens[$numSubTokens-1];
		$subImgTokens = explode(".", $imgFile);
		
		$imageID = $subImgTokens[0];
		
    //create prefix1
		$namePrefix1 = "";
		
		if ($extID != "-")
			$namePrefix1 = $extID;
		if ($tissue != "-")
			$namePrefix1 .= "_".$tissue;
		
		//create prefix2
    $namePrefix2 = "";
    
    if ($stain != "-")
			$namePrefix2 = $stain;
		if ($imageID != "-")
			$namePrefix2 .=	"_".$imageID;
			
		//get annotation
		$ann = requestAnnotation($imageID, $username, $password);
		
		if (strpos($ann, "Invalid userid/password:") !== FALSE)
		{
			fclose($indexFile);
			return "ERROR,ERROR: Invalid userid/password: Aperio ImageServer";
		}
		
		fwrite($indexFile, $namePrefix1.",".$namePrefix2.",".$loc.",".$imageID."\n");
		file_put_contents($workFolder."/".$imageID.".xml", $ann);
		
  }
  
  fclose($indexFile);
}

function requestAnnotation($id, $username, $password)
{
//  $baseUrl = 'http://129.43.1.24/';
  $baseUrl = 'http://fr-s-lsp-spc-d/';
  
  $curl_handle = curl_init();
  curl_setopt($curl_handle, CURLOPT_URL, $baseUrl.'@'.$id.'?GETANNOTATIONS');
  curl_setopt($curl_handle, CURLOPT_RETURNTRANSFER, true);
  curl_setopt($curl_handle, CURLOPT_USERPWD, $username.':'.$password);
  curl_setopt($curl_handle, CURLOPT_HTTPAUTH, CURLAUTH_BASIC);
  $html = curl_exec($curl_handle);
  
  curl_close($curl_handle);
  
  return $html;
}

function preProcess()
{
  clearHistory(5);
/*  
  if (empty($_FILES["file"]["name"]))
  {
    echo "ERROR,ERROR: It doesn't look like you have uploaded a valid file. Please go back and do it again.";
    return;
  }
*/

  $username = "guest";
  $password = "";
  
  if ($_POST["usernameManual"] != null || $_POST["passwordManual"] != null)
  {
    $username = $_POST["usernameManual"];
    $password = $_POST["passwordManual"];
  }
    
  //prepare a workfolder
  $id = mt_rand();
  
  $workFolder = "workspace/".$id."/";
  exec("mkdir ".$workFolder);
  
  $indexFile = $workFolder."index.csv";
  
  //query Spectrum database for annotations
  $message = prepareInputs($indexFile, $username, $password, $workFolder);

	if (filesize($indexFile) == 0)
		$message = "ERROR,ERROR: Empty index file found. Job aborted.";
		
	if ($message != "")
		echo $message;
	else
		echo $id;
}

?>

<!DOCTYPE html>
<html lang="en">
  <head>
    <meta http-equiv="Content-Type" content="text/html;charset=utf-8">
    <title>Aperio Image ROI Extraction - IVG - ABCC - ISP - Leidos Biomed</title>
    <link href="bootstrap/css/bootstrap.css" rel="stylesheet">
    <script type="text/javascript" src="d3/d3.js"></script>
    <script type="text/javascript" src="bootstrap/js/jquery.js"></script>
    <script type="text/javascript" src="bootstrap/js/bootstrap.js"></script>
  </head>
  <body>
    <div class="container">
      <div class="row"><div class="span12"><h1>Aperio Image ROI Extraction Workflow (beta)</h1></div></div>
      <div class="row"><div class="span12"><h4>Imaging and Visualization Group<br>Advanced Biomedical Computing Center</h4></div></div>
      <hr class="featurette-divider">
      <div class="row"><div class="span10" id="identifier"><img src="img/ajax-loader-bar.gif"></div></div>
      <div class="row"><div class="span12" id="reportTable"></div></div>
      <script type="text/javascript">
        var info = "<?php preProcess();?>";
        var infoArray = info.split(',');
        var id;
        
//        doReport("");
        
        if (infoArray[0] == "ERROR")
        {
					document.getElementById("identifier").innerHTML = "<h2>" + infoArray[1] + "</h2>";
				}
				else
				{
					id = infoArray[0];
					
					$.ajax({
						type: "POST",
						url: "workflow2_backend.php",
						data: {folder: id},
						success: function (result){ doReport(result);}
					});
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
					var reportArray = new Array;
					
					var line = new Object;
					line.id = -1;
					line.layer = -1;
					line.images = "";
						
					var imgID = -1;
						
					data.forEach(function(d){
						d.type = +d.type;
							
						if (d.type == 0)
						{
							imgID = d.value;
						}
						else if (d.type == 1)
						{
							reportArray.push(line);
								
						  line = new Object;
							line.id = imgID;
							line.layer = d.value;
							line.images = "";
						}
						else
						{
							line.images += ",";
								
							var name = d.value.slice(0, d.value.lastIndexOf(".tif"));
							name += ".jpg";
								
							line.images += name;
						}
					});
					
					reportArray.push(line);
					
					reportArray.shift();
					
					return reportArray;
				}
						
				function doReport(result)
        {
					var results = result.split(",");
					
					document.getElementById("identifier").innerHTML = "<h4>" + results[0] + " " + results[1] + "<br>" + results[2] + " (" + id + ")</h4>";
					
					d3.csv("workspace/" + id + "/result.csv", function(error, data){
						
						var reportArray = createImageGroup(data);
						
						console.log(reportArray);
						
						var message = "<table class='table table-striped'><tr><th>Image ID</th><th>Annotation Layer</th><th>Extracted ROIs</th><th>Thumbnails</th></tr>";
						
						reportArray.forEach(function(d){
							var imgs = d.images.split(",");
							imgs.shift();
							
							message += "<tr><td>" + d.id + "</td><td>" + (+d.layer+1) + "</td><td>" + imgs.length + "</td><td>";
							
							imgs.forEach(function(o){
								var linkStr = "<a href='workspace/" + id + "/output_p/" + d.id + "/" + o + "' target='_blank'>";
								message += linkStr;
								message += "<img class='img-polaroid' src='" + "workspace/" + id + "/output_s/" + d.id + "/" + o + "'>";
								message += "</a>";
							});
							
							message += "</td></tr>";
						});
						
						message += "</table>";
						
						document.getElementById("reportTable").innerHTML = message;

					});//d3.csv
				}
      </script>
    </div>
  </body>
</html>
