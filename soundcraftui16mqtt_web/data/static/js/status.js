function send_message(msg, topic){
  var message = new Paho.Message(msg);
  message.destionationName = "database_request/" + client.clientId + "/" + topic;
  client.send(message);
}

function onConnect() {
  // Once a connection has been made, make a subscription and send a message.
  client.subscribe("database_update/all/#");
  client.subscribe("database_update/" + client.clientId + "/#");
  client.subscribe("webpage/#");
  console.log("Mqtt Client connected");
  // TODO: Update UI
}

function onConnectionLost(responseObject) {
  if (responseObject.errorCode !== 0) {
    console.log("onConnectionLost:"+responseObject.errorMessage);
  }
  // TODO: Update some Elements in the UI
}
function onMessageArrived(message) {
  console.log("onMessageArrived:"+message.payloadString);
}

window.addEventListener("load", function(){
  broker_host = $("#mqtt_data").attr("host");
  broker_port = $("#mqtt_data").attr("port");
  var client = new Paho.Client(broker_host, Number(broker_port), uuid4());

  // set callback handlers
  client.onConnectionLost = onConnectionLost;
  client.onMessageArrived = onMessageArrived;

  // connect the client
  client.connect({onSuccess:onConnect});
}
