function onConnect() {
  // Once a connection has been made, make a subscription and send a message.
  window.mqtt_client.subscribe("database_update/all/#");
  window.mqtt_client.subscribe("database_update/" + window.mqtt_client.clientId + "/#");
  window.mqtt_client.subscribe("webpage/#");
  console.log("Mqtt Client connected");
  // $("#btn-mqtt").removeClass("btn-danger").addClass("btn-success");
}

function onConnectionLost(responseObject) {
  if (responseObject.errorCode !== 0) {
    console.log("onConnectionLost:"+responseObject.errorMessage);
  }
  // $("#btn-mqtt").removeClass("btn-success").addClass("btn-danger");
}
function onMessageArrived(message) {
  console.log("Message arrived on topic " + message.destinationName + " with content " + message.payloadString);
}
