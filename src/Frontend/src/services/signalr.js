import { HubConnectionBuilder, LogLevel } from '@microsoft/signalr';

export const connection = new HubConnectionBuilder()
    .withUrl('/hub')
    .configureLogging(LogLevel.Information)
    .withAutomaticReconnect()
    .build();

export const startConnection = async () => {
    try {
        await connection.start();
        console.log('SignalR Connected.');
    } catch (err) {
        console.log('SignalR Connection Error: ', err);
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
    return connection.invoke(methodName, ...args);
};
