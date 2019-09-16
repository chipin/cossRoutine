<?php
  $now = date("Y/m/d H:i:s");
  //$WSDL_URL = 'http://172.16.13.30/TWM_AXIS/axis2/services/ForwardAlarm?wsdl';
  $WSDL_URL = 'http://10.222.14.12:8080/axis2/services/ForwardAlarm?wsdl';

  $data = array('objectName' => '3404611',
                'alarmName' => 'CM Status: Offline',
                'severity' => 'Critical',
                'probableCause' => 'Status Error',
                'description' => 'Address',
                'eventDateTime' => $now,
                'alarmNumber' => 'OEMS ID: 238857',
                'system' => 'TFM CM',
                'networkElement' => 'PHC',
                'module' => 'CM',
                'neGroup' => 'CM'
  );

  $xmlstr = '';
  while (list($k,$v)=each($data)) {
    $xmlstr .= "<$k>" . $v . "</$k>";
  }
  if (!empty($xmlstr)) $xmlstr = '<alarm>' . $xmlstr . '</alarm>';
  echo $xmlstr . "\n";

  try {
    $client = new SoapClient($WSDL_URL, array('encoding' => 'UTF-8', 'trace' => 1, 'exceptions' => 1, 'cache_wsdl' => 'WSDL_CACHE_NONE', 'connection_timeout' => 10,
    'location' => $WSDL_URL));
  }
  catch (Exception $err) {
    die('Error: Could not connect to PIsysWebService!');
  }

  var_dump($client->__getFunctions());
  var_dump($client->__getTypes());

  $xmlstr = '';
  try {
    $res = $client->ForwardAlarm(array('alarm' => $xmlstr));
  }
  catch (Exception $err) {
    echo 'Caught exception: ',  $e->getMessage(), "\n";
    die('Error: Could not CALL ForwardAlarm!');
  }

  print_r($res);

  echo "REQUEST:\n" . $client->__getLastRequest() . "\n";
  echo "REQUEST HEADERS:\n" . $client->__getLastRequestHeaders() . "\n";
  echo "RESPONSE:\n" . $client->__getLastResponse() . "\n";
  echo "RESPONSE HEADERS:\n" . $client->__getLastResponseHeaders() . "\n";
  echo $res->return . "\n";
?>
