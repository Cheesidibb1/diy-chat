// client.js
let chathost = window.location.host;
const socket = new WebSocket(`ws://${chathost}/ws`);

socket.addEventListener('open', event => {
  console.log('Connected to WebSocket server');
  socket.send('Hello from client!');
});

socket.addEventListener('message', event => {
  console.log(`Received: ${event.data}`);
});

socket.addEventListener('close', event => {
  console.log('Disconnected from WebSocket server');
});

socket.addEventListener('error', event => {
  console.error('WebSocket error:', event);
});