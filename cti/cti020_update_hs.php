<?php
  include_once('common.inc.php');

  $now = date("Y-m-d H:i:s");
  echo "START: $now\n\n";

  $ora  = GetDBH('CNIS','CTI');
  $hsdb = GetDBH('HS');

  $sql = "select flag,cti_id,companyno,subsid,singlesn,smartcard,case when packagename like '%店家%' or billitem like '%店家%' then 'store' else 'hs' end pkg
          from cti020
          where instime >= sysdate-10 and servicename='C HS' and (to_char(subsid)=singlesn or singlesn is null or smartcard is not null)
          order by instime";
  $sth = oci_parse($ora, $sql);
  oci_execute($sth);
  while ($row = oci_fetch_assoc($sth)) {
    $flag = $row['FLAG'];
    $cti_id = $row['CTI_ID'];
    $so = $row['COMPANYNO'];
    $subsid = $row['SUBSID'];
    $pkg = $row['PKG'];
    $singlesn = $row['SINGLESN'];

    echo "$flag, $cti_id, $so, $subsid, $pkg, $singlesn\n";

    $dipsid_arr = array();
    $dipsid_str = '';

    if ($pkg == 'store') {
      $mysql = "select s.so,s.subsid,s.status store_status,n.storeid,n.id nvrid,n.deviceid dips_id,n.name device_name,n.status nvr_status
                from store.store s
                inner join store.nvr n on n.storeid=s.id and n.status = 1
                where s.so='$so' and s.subsid='$subsid' and s.status > -3";
    }
    else {
      $mysql = "select dips_id from dips_device where so='$so' and subsid='$subsid'";
    }
    $myresult = mysql_query($mysql,$hsdb);
    while ($myrow = mysql_fetch_assoc($myresult)) {
      array_push($dipsid_arr, $myrow['dips_id']);
    }

    if (count($dipsid_arr)) $dipsid_str = implode(";", $dipsid_arr);

    echo "=> $dipsid_str\n";

    if (!empty($dipsid_str)) {
      $sql2 = "update cti020 set singlesn='$dipsid_str',smartcard='' where companyno='$so' and cti_id='$cti_id'";
      echo "=> $sql2\n";
      $sth2 = oci_parse($ora, $sql2);
      oci_execute($sth2);
    }

  }

  $now = date("Y-m-d H:i:s");
  echo "\nEND: $now\n\n";
?>
