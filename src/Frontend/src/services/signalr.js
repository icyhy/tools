import { HubConnectionBuilder, LogLevel, HubConnectionState } from '@microsoft/signalr';
import { ref } from 'vue';

export const connectionState = ref('disconnected');

export const connection = new HubConnectionBuilder()
    .withUrl('/hub')
    .configureLogging(LogLevel.Information)
    .withAutomaticReconnect({
        nextRetryDelayInMilliseconds: retryContext => {
            if (retryContext.elapsedMilliseconds < 60000) {
                return Math.random() * 2000 + 1000; // 1-3 seconds
            } else {
                return 5000; // 5 seconds after 1 minute
            }
        }
    })
    .build();

// Update connection state on events
connection.onreconnecting(() => {
    connectionState.value = 'reconnecting';
    console.log('SignalR Reconnecting...');
});

connection.onreconnected(() => {
    connectionState.value = 'connected';
    console.log('SignalR Reconnected.');
});

connection.onclose(() => {
    connectionState.value = 'disconnected';
    console.log('SignalR Connection Closed.');
});

export const startConnection = async () => {
    if (connection.state === HubConnectionState.Connected) {
        console.log('SignalR already connected.');
        return;
    }
    
    try {
        await connection.start();
        connectionState.value = 'connected';
        console.log('SignalR Connected.');
    } catch (err) {
        connectionState.value = 'error';
        console.error('SignalR Connection Error: ', err);
        setTimeout(startConnection, 5000);
    }
};

export const on = (methodName, newMethod) => {
    connection.on(methodName, newMethod);
};

export const off = (methodName) => {
    connection.off(methodName);
};

export const invoke = async (methodName, ...args) => {
    try {
        if (connection.state !== HubConnectionState.Connected) {
            throw new Error('SignalR not connected');
        }
        return await connection.invoke(methodName, ...args);
    } catch (err) {
        console.error(`Failed to invoke ${methodName}:`, err);
        throw err;
    }
};

export const getConnectionState = () => {
    return connection.state;
};
