window.addEventListener("load", function(){
  broker_host = $("#mqtt_data").attr("host");
  broker_port = $("#mqtt_data").attr("port");
  var client = new Paho.Client(broker_host, Number(broker_port), uuid4());
  window.mqtt_client = client;

  // set callback handlers
  window.mqtt_client.onConnectionLost = onConnectionLost;
  window.mqtt_client.onMessageArrived = onMessageArrived;

  // connect the client
  window.mqtt_client.connect({onSuccess:onConnect});
});
