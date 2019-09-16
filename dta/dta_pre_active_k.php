<?php
  //header("Content-Type: text/html; charset=big5");

  require_once 'conn_db.inc.php';
  require_once('common.inc.php');
  require_once("web_get.php");

  //$SOlist = array('101','103','104','300','701','210','220','230','240','250','260','106','310','330','420','610','820','810','410');
  

  $SOlist = array('820');
  $now = date("Y-m-d H:i:s");

  $today = date("Y-m-d");
  $yday = date("Y-m-d",strtotime('-7 day'));

  echo "START: $now\n\n";

  $ora_dbh = new CONN_DB("SCNIS_COSS");
  $coss_dbh = getDBH('CNIS','COSS');
  //$ora_dbh = getDBH("CNIS","COSS");

  $pre_list = $dta_list = array();

  echo date("Y-m-d H:i:s") . ": query all ca_dta\n";



  echo "pre_list: " . count($pre_list) . "\n";

  foreach($SOlist as $so) {
    $pre_list = array();
    if (preg_match("/^\d+$/i", $so)) {
      echo date("Y-m-d H:i:s") . ": query $so MI\n";

      $SQL = "select stbno,nuid,iccno,mi,provtime,case when provtime is not null and iccno is not null then '2' else '1' end flag from ca_dta where so='$so' or so is null "; // 2已開通, 1未開通
      echo $SQL;
      $ora_dbh->query_all($SQL);

      foreach($ora_dbh->Record as $row) {
        $dta_list[$row['STBNO']] = $row['FLAG'];
        if ($row['MI']=='N' ) {
          $pre_list[$row['STBNO']] = $row['NUID'];
        }
      }
      $stbno_list = $pre_list; //MI=N為基本數量


      if($so == '106') {
        $cossdbh = new CONN_DB("CossMS_CG");
        //$SQL = "select singlesn,nuid from mi0130 with (nolock) where companyno='$so' and placeno='開通準備倉' and singlesn is not null";
        $SQL = "select b.singlesn,b.nuid from mi3020 a with(nolock) left join mi0130 b with(nolock)
                on a.companyno = b.companyno and a.singlesn = b.singlesn
                where a.createtime >= '$yday' and a.createtime <= '$today' and a.companyno = '$so' and a.swversion = 'DTA'
                and b.placeno='開通準備倉' and b.singlesn is not null";
      }
      else if (!preg_match("/^(101|103|104|300|701|500)$/i", $so)) {
        $cossdbh = new CONN_DB("kbroCossMS");
        //$SQL = "select singlesn,nuid from mi0130 with (nolock) where companyno='$so' and placeno='開通準備倉' and singlesn is not null and createtime > '2014-09-10 00:00:00' ";
        $SQL = "select b.singlesn,b.nuid from mi3020 a with(nolock) left join mi0130 b with(nolock)
                on a.companyno = b.companyno and a.singlesn = b.singlesn
                where a.createtime >= '$yday' and a.createtime <= '$today' and a.companyno = '$so' and a.swversion = 'DTA'
                and b.placeno='開通準備倉' and b.singlesn is not null ";
      }
      else {
        $cossdbh = new CONN_DB('TFMCossMS');
        $SQL = "select singlesn,nuid_barcode nuid from nwis0020 with(nolock) where companyno='$so' and nuid_barcode is not null and mtkind='STB' and instore='N'";
      }
      $cossdbh->query_all($SQL);
      foreach($cossdbh->Record as $row) {
        $p_stbno = $row['SINGLESN'];
        if(empty($p_stbno)) $p_stbno = $row['singlesn'];

        $p_nuid = $row['NUID'];
        if(empty($p_nuid)) $p_nuid = $row['nuid'];

        $stbno_list[$p_stbno] = $p_nuid;

        /*
        if(!empty($p_stbno))
        {
          $SQL = "update ca_dta set ready='Y' where stbno='".$p_stbno."'";
          $ora_dbh->execute($SQL);
        }
        */
      }
      $cossdbh->close();

      if (empty($stbno_list)) {
        echo date("Y-m-d H:i:s") . ": stbno_list is empty\n";
        continue;
      }

      echo date("Y-m-d H:i:s") . ": array_diff\n";
      echo "stbno_list: " . count($stbno_list) . "\n";
      echo "dta_list:   " . count($dta_list) . "\n";

      $num1 = $num2 = 0;
      while (list($k1, $v1) = each($stbno_list)) {
        if (preg_match("/^\d+$/i", $k1) && preg_match("/^\d+$/i", $v1)) {
          if (empty($dta_list[$k1])) {
            $num1++;
            $dta_list[$k1] = 2; // 避免重覆insert, 此時無SmartCard也無法開通, 故假裝成已開通
            $SQL = "insert into ca_dta(stbno,nuid,so) values('$k1','$v1','$so')";
            echo "$SQL\n";

            $sth = oci_parse($coss_dbh,$SQL);
            //if ($num1%50 == 0) 
            oci_execute($sth);
            //$ora_dbh->execute($SQL);
            //if ($num1%50 == 0) $ora_dbh->commit();

          }

          if (empty($dta_list[$k1]) || $dta_list[$k1] != 2) {
            $num2++;
            $dta_list[$k1] = 2; // 避免重覆開通
            $query_str = 'so='.$so.'&stbno='.$k1.'&func=PRE_ACT&account=PRE_ACTIVE';
            echo "$query_str\n";
            $result_str = web_service_get("http://172.16.13.72/GW/dtv/dta_prov.php?".$query_str, "");
            if($result_str=='OK') {
              $SQL = "update ca_dta set provtime=sysdate where stbno='$k1'";
              echo "$SQL\n";
              $ora_dbh->execute($SQL);
              if ($num2%50 == 0) $ora_dbh->commit();
            }
            else
              echo 'ERROR: PROV fail, ' . $result_str . "\n";
          }
        }
        else {
          echo 'ERROR: ' . $k1 . ',' . $v1 . ' is incorrect format' . "\n";
        }
      }
      if ($num1 > 0 || $num2 > 0) $ora_dbh->commit();
    }
    else {
      echo 'ERROR: ' . $so . ' is incorrect format' . "\n";
    }
  }

  $ora_dbh->close();

  $now = date("Y-m-d H:i:s");
  echo "\nEND: $now\n";
?>
