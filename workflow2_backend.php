
<?php

//echo phpinfo();

function getSafeInputValue($input)
{
  $output = trim(rtrim($input));
  
  if (strlen($output) > 0)
  {
		$output = str_replace(" ", "-", $output);
		$output = str_replace("/", "-", $output);
	}
  else
    $output = "-";
  
  return $output;
}

function getNumOfROIs($path)
{
  $rois = 0;
  
  if ($handle = opendir($path))
  {
    while (false !== ($entry = readdir($handle)))
    {
      if ($entry != "." && $entry != "..")
      {
        if (is_dir($path."/".$entry))
        {
          $files = scandir($path."/".$entry);
          $rois += count($files) - 2;
        }
      }
    }
    
    closedir($handle);
  }
  
  return $rois;
}

function postProcess($path)
{
  if ($handle = opendir($path))
  {
    while (false !== ($entry = readdir($handle)))
    {
      if ($entry != "." && $entry != "..")
      {
        $folder = $path."/".$entry;
        
        if (is_dir($folder))
        {
#          shell_exec("gm mogrify -compress LZW ".$folder."/*.tif");
          shell_exec("gm mogrify -profile profile.icc ".$folder."/*.tif");
        }
      }
    }
    
    closedir($handle);
  }
}

function getProcessTime($period)
{
  $minutes = 0;
  $seconds = 0;
      
  if ($period > 60)
    $minutes = intval($period / 60);
      
  $seconds = $period - $minutes * 60;
     
  return $minutes." minutes ".$seconds. " seconds";
}

function prepareThumbnails($path)
{
  if ($handle = opendir($path))
  {
    while (false !== ($entry = readdir($handle)))
    {
      if ($entry != "." && $entry != "..")
      {
        $folder = $path."/".$entry;
        
        if (is_dir($folder))
        {
          shell_exec("gm mogrify -resize 100x100 ".$folder."/*.jpg");
        }
      }
    }
    
    closedir($handle);
  }
}

function prepareJPGs($path)
{
  if ($handle = opendir($path))
  {
    while (false !== ($entry = readdir($handle)))
    {
      if ($entry != "." && $entry != "..")
      {
        $folder = $path."/".$entry;
        
        if (is_dir($folder))
        {
          shell_exec("gm mogrify -resize 1024x1024\> -format jpg -quality 75 ".$folder."/*.tif");
          shell_exec("rm -rf ".$folder."/*.tif");
        }
      }
    }
    
    closedir($handle);
  }
}

function parseXML($fileName)
{
  $annotations = simplexml_load_file($fileName);
 
  $outputFileROI = fopen($fileName.".roi", "w");
  $outputFileLine = fopen($fileName.".line", "w");
    
  $layerCount = 0;
    
  #each layer
  foreach ($annotations->Annotation as $anno)
  {
    $layerCount ++;
    $layerNameStr = "";
    
    foreach ($anno->Attributes->Attribute as $attr)
    {
      $name = (string)$attr['Name'];
      $value = (string)$attr['Value'];
        
      if (!empty($value))
        $layerNameStr = $value;
      elseif (!empty($name) && strcmp($name, "Description") != 0)
        $layerNameStr = $name;
      else
        $layerNameStr = (string)$layerCount;
        
      $layerNameStr = getSafeInputValue($layerNameStr);
    }
      
    $lineAnno = array();
    $roiAnno = array();
      
    #each region
    foreach ($anno->Regions->Region as $region)
    {
      $type = (int)$region['Type'];
        
      #0: poly line
      if ($type == 0)
        array_push($lineAnno, (string)$region['LengthMicrons']);
      elseif ($type == 1)#1: box
      {
        foreach ($region->Vertices as $roi)
        {
          $roiArray = array();
          foreach ($roi->Vertex as $vertex)
          {
            array_push($roiArray, (string)$vertex['X']);
            array_push($roiArray, (string)$vertex['Y']);
          }
            
          array_push($roiAnno, $region['DisplayId'].",".implode(",", $roiArray));
        }
      }
    }#end of region processing
      
    if (!empty($lineAnno))
      fwrite($outputFileLine, $layerNameStr.",".implode(",", $lineAnno)."\n");
      
    foreach ($roiAnno as $roi)
      fwrite($outputFileROI, $layerNameStr.",".$roi."\n");
  }
    
  fclose($outputFileLine);
  fclose($outputFileROI);
}

function processROIs($workFolder, $outputFolder)
{
  //load index.csv file
  $indexCSV = fopen($workFolder."index.csv", "r");
  
  $reportFileName = $workFolder."result.csv";
  
  $reportFile = fopen($reportFileName, "w");
  fputcsv($reportFile, array('ImageID', 'LayerName', 'ROIFile'));
  fclose($reportFile);
  
  while(! feof($indexCSV))
  {
    $line = fgetcsv($indexCSV);
    
    $prefix = $line[0];
    $postfix = $line[1];
    $location = $line[2];
    $imageID = $line[3];
    
    $annFile = $workFolder.$imageID.".xml";
    
    if (file_exists($annFile))
    {
      parseXML($annFile);
      
      if (filesize($annFile.".roi") != 0)
      {
        //create output folder for current image
        $roiFolder = $outputFolder.$imageID;
        exec("mkdir ".$roiFolder);
        
        $exec_name = "aux/Aperio_Extract_ROI";
        
        //process ROIs for current image
        exec($exec_name." ".$annFile.".roi"." ".$roiFolder." ".$prefix." ".$postfix." ".$location." ".$reportFileName." ".$imageID." >> ".$workFolder."output.txt");
      }
    }
  }
  
  fclose($indexCSV);
}

function processLines($workFolder)
{
  //load index.csv file
  $indexCSV = fopen($workFolder."index.csv", "r");

  $lineAnnArray = array();
  
  while(! feof($indexCSV))
  {
    $line = fgetcsv($indexCSV);
    
    $prefix = $line[0];
    $postfix = $line[1];
    $location = $line[2];
    $imageID = $line[3];
    
    $annFile = $workFolder.$imageID.".xml".".line";
    
    if (file_exists($annFile) && filesize($annFile) != 0)
    {
      $lines = fopen($annFile, "r");
      
      while (! feof($lines))
      {
        $annArray = array($prefix."_".$postfix);
        
        $ann = fgetcsv($lines);
        
        if (count($ann) > 1)
        {
          foreach ($ann as $token)
            array_push($annArray, $token);
          
          array_push($lineAnnArray, $annArray);
        }
      }
      
      fclose($lines);
    }
  }
  
  fclose($indexCSV);

  if (count($lineAnnArray) > 0)
  {
    $lineAnn = fopen($workFolder."lineAnn.csv", "w");
    
    fwrite($lineAnn, "Annotation line length data\n\n");
    fwrite($lineAnn, "Specimen,Layer,Total Length(um)\n");
    
    foreach ($lineAnnArray as $line)
    {
      $total = 0;
      for ($i = 2; $i < count($line); ++$i)
        $total += floatval($line[$i]);
        
      $newArray = array($line[0], $line[1], $total);
      fputcsv($lineAnn, $newArray);
    }
    
    fwrite($lineAnn, "\nSpecimen,Layer,Total Length(um)\n");
    
    foreach($lineAnnArray as $line)
    {
      fputcsv($lineAnn, $line);
    }
    
    fclose($lineAnn);
  }
}

function process()
{
	$id = $_POST["folder"];
  
  if (!is_numeric($id))
  {
		echo "Incorrect job id submitted. Job has been aborted.";
		return;
	}
	
  $workFolder = "workspace/".$id."/";
  
  $outputFolder = $workFolder."output/";
  exec("mkdir ".$outputFolder);
  
//  $exec_name = "aux/Aperio_Extract_ROI_xml";
  
  $startTime = time();
  
  //process all ROIs
  //exec($exec_name." ".$workFolder." ".$outputFolder." >> ".$workFolder."output.txt");
  processROIs($workFolder, $outputFolder);
  processLines($workFolder);
  
  //LZW zip (can not be done in ITK)
  //embeded color profile
  postProcess($outputFolder);
  
  $endTime = time();
  
  $timeStamp = date('Y-m-d_h-i_a', time());
  
  //copy to nfs mount
  $nfsMount = "nfsMount/";
//  $nfsMount = "/shared/imaging_workflows/workflow_two/imaging_share/tacl_share/";
  $remoteFolder = $timeStamp;
  
  /*copy output folder*/
//  exec("cp -R ".$outputFolder." ".$nfsMount.$remoteFolder);
//  exec("chmod -R 777 ".$nfsMount.$remoteFolder);
  /*end of copying output folder*/
  
  $zipFile = $timeStamp.".zip";
  exec("cd ".$outputFolder."; "." zip -r -0 ../".$zipFile." .; cd ../../../");
  
  $zipFile = $workFolder.$zipFile;
    
  $fs = filesize($zipFile) / (1024*1024);
  $unit = "MB";
    
  if ($fs < 0.001)
  {
    $fs = filesize($zipFile) / 1024;
    $unit = "KB";
  }
    
  $processTime = getProcessTime($endTime - $startTime + 1);
  $numROIs = getNumOfROIs($outputFolder);
  
  $lines = file($workFolder."index.csv", FILE_IGNORE_NEW_LINES);
  $numImages = sizeof($lines);
  
  //write log file
  {
    $logFile = fopen("log/access.txt","a") or exit("Unable to open log file!");
      
    while(!flock($logFile, LOCK_EX))
    {
      sleep(mt_rand(1,10));
    }
    
    $date = date('m/d/Y h:i:s a', time());
    
    fwrite($logFile, $numImages.",".$numROIs.",".$date.",".$processTime.",".$_SERVER['REMOTE_ADDR']."\n");
      
    fflush($logFile);
    flock($logFile, LOCK_UN);
      
    fclose($logFile);
  }
  
  $thumbStartTime = time();
  
  $previewFolder = $workFolder."output_p/";
  exec("cp -r ".$outputFolder." ".$previewFolder);
  
  prepareJPGs($previewFolder);
  
  $thumbnailFolder = $workFolder."output_s/";
  exec("cp -r ".$previewFolder." ".$thumbnailFolder);
  
  prepareThumbnails($thumbnailFolder);
  
  $thumbEndTime = time();
    
  $thumbProcessTime = getProcessTime($thumbEndTime - $thumbStartTime + 1);
  
  $downloadLink = sprintf("<a href='".$zipFile."'>Download ROIs (%.2f %s)</a>, ", $fs, $unit);
  
  $lineAnnFile = $workFolder."lineAnn.csv";
  
  if (file_exists($lineAnnFile))
		$downloadLink .= "<a href='".$lineAnnFile."'>Download Line Annotations</a>";
  
  echo $numROIs." ROIs extracted in ".$processTime.",".$downloadLink.",".$remoteFolder;
}

process();

?>
