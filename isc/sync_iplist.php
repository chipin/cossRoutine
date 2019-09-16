<?php
  /* 20190215 */
  header("Content-Type:text/html; charset=utf-8");
  include_once('common.inc.php');
  
  $dbh_cnis = GetDBH('CNIS');
  $dbh_isc_m = GetDBH('ISC_M','ecnis');  
  $dbc_kbro = GetDBH('KBRO_NMSDB','NMS_CM');
      
	echo "\n start ".date("Y/m/d H:i:s")."\n";
	$data = get_1();	
	insert_ip_list(1,$data);
	$data = get_2();
	insert_ip_list(2,$data);
	$data = get_3();
	insert_ip_list(3,$data);
	$data = get_4();
	insert_ip_list(4,$data);
	
	echo "\n end ".date("Y/m/d H:i:s")."\n";		
	oci_close($dbh_cnis);
	mysql_close($dbh_isc_m);	
	oci_close($dbc_kbro);
	
	function insert_ip_list($sort,$data) {
		sleep(1);						
		global $dbh_isc_m;		
		foreach ($data as &$val) {
			unset($sql);
			if ($sort==2) {
				$companyno = $val['SO'];
			} else {
				$companyno = $val['COMPANYNO'];
			}
			$type = $val['TYPE'];			
			if ($sort==3) {
				$maker = $val['VENDOR'];
			} else {
				$maker = $val['MAKER'];
			}			
			$model = $val['MODEL'];
			$ne_id = $val['NE_ID'];
			$ip = $val['IP'];
			$community = $val['SNMP_RO'];
			$stopyn = $val['STOPYN'];
			$remark = $val['REMARK'];				
			$scope = $val['SCOPE'];
			$mxlpbkip = $val['MXLPBKIP'];
			$telnetid = $val['TELNETID'];
			$telnetpwd = $val['TELNETPWD'];
			$header = $val['HEADER'];
			$sql = "replace into IP_LIST(companyno,type,maker,model,ne_id,ip,community,stopyn,remark,scope,mxlpbkip,telnetid,telnetpwd,header,updatetime) values ('".$companyno."','".$type."','".$maker."','".$model."','".$ne_id."','".$ip."','".$community."','".$stopyn."','".$remark."','".$scope."','".$mxlpbkip."','".$telnetid."','".$telnetpwd."','".$header."',now())";
			//echo "<br>\n".$sql;
			@mysql_query($sql,$dbh_isc_m);				
		}    
  }	
	
	function get_1() {
		sleep(1);				
		global $dbh_cnis;						
		$sql = "select companyno,'CMTS' as type ,(select maker from sys_object where stopyn='N' and ne_id=substr(a.cmts_id,-8,4)) maker
,(select model from sys_object where stopyn='N' and ne_id=substr(a.cmts_id,-8,4)) model,
cmts_id as ne_id,ip,snmp_ro,stopyn,remark,scope,mxlpbkip,'' as telnetid ,'' as telnetpwd,'' as header,sysdate from cmts a where --stopyn = 'N'
(updatetime > to_date('2019/03/11 00:00:00','YYYY/MM/DD HH24:MI:SS') 
or createtime > to_date('2019/03/11 00:00:00','YYYY/MM/DD HH24:MI:SS'))

union 

select companyno,type,(select maker from sys_object where stopyn='N' and ne_id=substr(a.ne_id,-8,4)) maker
,(select model from sys_object where stopyn='N' and ne_id=substr(a.ne_id,-8,4)) model,
ne_id,ip,snmp_ro,stopyn,remark,scope,'' as mxlpbkip  , '' as telnetid ,'' as telnetpwd,'' as header, sysdate from ip_ne a where --stopyn = 'N' 
(updatetime > to_date('2019/03/11 00:00:00','YYYY/MM/DD HH24:MI:SS') 
or createtime > to_date('2019/03/11 00:00:00','YYYY/MM/DD HH24:MI:SS'))
and type in ('CoreRouter','Switch','DCN','Firewall','Gpon','QAM','Cache','CGNAT')


union 

select companyno,'CNR' as type,(select maker from sys_object where stopyn='N' and ne_id=substr(a.cnr_id,-8,4)) maker
,(select model from sys_object where stopyn='N' and ne_id=substr(a.cnr_id,-8,4)) model,
cnr_id as ne_id,ip,'',stopyn,remark,'' as scope,'' as mxlpbkip  , '' as telnetid ,'' as telnetpwd,header, sysdate from cnr a where --stopyn = 'N' 
(updatetime > to_date('2019/03/11 00:00:00','YYYY/MM/DD HH24:MI:SS') 
or createtime > to_date('2019/03/11 00:00:00','YYYY/MM/DD HH24:MI:SS'))

union 

select companyno,'LS' as type,(select maker from sys_object where stopyn='N' and ne_id=substr(a.olt_id,-8,4)) maker
,(select model from sys_object where stopyn='N' and ne_id=substr(a.olt_id,-8,4)) model,
olt_id as ne_id,ip,snmp_ro,stopyn,remark,'' as scope, '' as mxlpbkip  , '' as telnetid ,'' as telnetpwd, '' as header, sysdate  from ls_olt a where --stopyn = 'N' 
(updatetime > to_date('2019/03/11 00:00:00','YYYY/MM/DD HH24:MI:SS') 
or createtime > to_date('2019/03/11 00:00:00','YYYY/MM/DD HH24:MI:SS'))
"; 
		
    $sth = oci_parse($dbh_cnis, $sql);
    oci_execute($sth);				
		unset($row);
		unset($tmp);  
		$tmp = array();
		while ($row = oci_fetch_assoc($sth)) { 	  		
			$tmp[] = $row;
		}			
		oci_free_statement($sth); 		
		return $tmp;	    
  }
  
  function get_2() {
		sleep(1);				
		global $dbc_kbro;				
		$sql = "select so,'kbro_FTTX' as type,ne_id,model,'' as maker,ip,'' as snmp_ro,case when monitor = 'Y' then 'N' else 'Y' end as stopyn,'' as remark,'' as scope, '' as mxlpbkip  , '' as telnetid ,'' as telnetpwd, '' as header, sysdate from fttb_v2sw --where monitor = 'Y'";
		$sth = oci_parse($dbc_kbro, $sql);
    oci_execute($sth);				
		unset($row);
		unset($tmp);  
		$tmp = array();
		while ($row = oci_fetch_assoc($sth)) { 	  		
			$tmp[] = $row;
		}			
		oci_free_statement($sth); 		
		return $tmp;	    
	}
	
	function get_3() {
		sleep(1);				
		global $dbh_cnis;				
		$sql = "SELECT '106' as companyno,a.ne_id,'CG_FTTX' as type , a.vendor, a.model, a.ip, vendor, 
                 a.snmp_ro, a.stopyn, a.remark, '' as scope,'' as mxlpbkip, a.account as telnetid, a.passwd as telnetpwd, '' as header, sysdate
          FROM cg_fttb a --where stopyn = 'N'";    
		$sth = oci_parse($dbh_cnis, $sql);
    oci_execute($sth);				
		unset($row);
		unset($tmp);  
		$tmp = array();
		while ($row = oci_fetch_assoc($sth)) { 	  		
			$tmp[] = $row;
		}			
		oci_free_statement($sth); 		
		return $tmp;	    
	}
	
	function get_4() {
		sleep(1);				
		global $dbh_cnis;						
		$sql = "select a.companyno,'TFM_FTTX' as type,a.eq_id as ne_id, '' as maker, a.sys_type as model, a.ip_dcn || '/' || a.ip_public as ip, a.community as snmp_ro, 
case when status='1' then 'N' else 'Y' end as stopyn, a.ass_desc as remark,'' as scope,'' as mxlpbkip, '' as telnetid, '' as telnetpwd, '' as header,sysdate
from tfm_fttx a inner join tfm_fttx_acl_mapping b on a.hid = b.hid inner join tfm_fttx_acl c on b.cata_id = c.cata_id  --where a.status = '1'
"; 		
    $sth = oci_parse($dbh_cnis, $sql);
    oci_execute($sth);				
		unset($row);
		unset($tmp);  
		$tmp = array();
		while ($row = oci_fetch_assoc($sth)) { 	  		
			$tmp[] = $row;
		}			
		oci_free_statement($sth); 		
		return $tmp;	    
  }
		
?>
