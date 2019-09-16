<?php
  /*
    請使用UTF-8 without BOM編碼
    Written by Swallow 2012.04.16
  */
  include_once('common.inc.php');

  $CossMS = array('TFM' => 'TFMCossMS', 'KBRO' => 'kbroCossMS', 'CG' => 'CossMS_CG');

  $dbh2 = GetDBH('CNIS');

  while (list($k, $v) = each($CossMS)) {
    $dbh = GetDBH($v);
    $sql = "select A.CompanyNo,A.SubsID,A.SubsName,A.CustStatus,A.SingleSN,B.NodeNo,B.LinkID,B.MSCity+B.MSDistrict+B.Addrname InstAddr,
            case when substring(A.CustStatus,1,1) in ('0','1','8','9') then 'N' else 'Y' end StopYN
            from MS0200 A with (nolock)
            inner join MS0102 B with (nolock) on B.CompanyNo=A.CompanyNo and B.CustID=A.CustID and B.AddrNo=0
            where A.ServiceName in ('2 CM') and A.SubsName like '%台灣大哥大%' and substring(A.CustStatus,1,1) not in ('3','4','5','6')
            order by A.CompanyNo,A.SubsID";
    $sth = mssql_query($sql, $dbh);
    while ($row = mssql_fetch_assoc($sth)) {
      $row = strfilter($row);

      $companyno = $row['CompanyNo'];
      $subsid = $row['SubsID'];
      $cmmac = $row['SingleSN'];
      $node = $row['NodeNo'];
      $link = $row['LinkID'];
      $instaddr = $row['InstAddr'];
      $stopyn = $row['StopYN'];

      echo "$companyno,$subsid,$cmmac,$node,$link,$instaddr,$stopyn\n";

      $exist_flag = 0;
      $sth2 = oci_parse($dbh2, "select * from cmmac_twm where companyno='$companyno' and subsid='$subsid'");
      oci_execute($sth2);
      while ($row2 = oci_fetch_assoc($sth2)) {
        $row2 = strfilter($row2);
        $exist_flag = 1;
      }

      if ($exist_flag == 1) {
        $sth3 = oci_parse($dbh2, "update cmmac_twm set stopyn='$stopyn',updatetime=sysdate where companyno='$companyno' and subsid='$subsid'");
        oci_execute($sth3);
      }
      else {
        $sth3 = oci_parse($dbh2, "insert into cmmac_twm (companyno,subsid,stopyn,updatetime) values ('$companyno','$subsid','$stopyn',sysdate)");
        oci_execute($sth3);
      }
    }
    mssql_close($dbh);
  }

  $sth2 = oci_parse($dbh2, "delete from cmmac_twm where updatetime < sysdate-1");
  oci_execute($sth2);

  oci_close($dbh2);
?>
