/**
 * useSocket - Hook para manejar conexión WebSocket con Socket.IO
 */
import { useEffect, useRef, useState } from 'react';
import { io } from 'socket.io-client';

const SOCKET_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

export function useSocket(syncCode) {
  const socketRef = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const [syncStatus, setSyncStatus] = useState(null);

  useEffect(() => {
    if (!syncCode) return;

    console.log('[WebSocket] Conectando a:', SOCKET_URL);

    // Crear conexión
    const socket = io(SOCKET_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5
    });

    socketRef.current = socket;

    // Event: connected
    socket.on('connect', () => {
      console.log('[WebSocket] Conectado');
      setIsConnected(true);

      // Unirse a la sala de sincronización
      socket.emit('join_sync', { sync_code: syncCode });
    });

    // Event: disconnected
    socket.on('disconnect', () => {
      console.log('[WebSocket] Desconectado');
      setIsConnected(false);
    });

    // Event: joined room
    socket.on('joined', (data) => {
      console.log('[WebSocket] Unido a sala:', data.room);
    });

    // Event: status_update
    socket.on('status_update', (data) => {
      console.log('[WebSocket] Status update:', data);
      setSyncStatus(data);
    });

    // Event: connection error
    socket.on('connect_error', (error) => {
      console.error('[WebSocket] Error de conexión:', error);
    });

    // Cleanup
    return () => {
      console.log('[WebSocket] Limpiando conexión');
      if (socket) {
        socket.emit('leave_sync', { sync_code: syncCode });
        socket.disconnect();
      }
    };
  }, [syncCode]);

  // Función para suscribirse a eventos personalizados
  const on = (event, callback) => {
    if (socketRef.current) {
      socketRef.current.on(event, callback);
    }
  };

  // Función para desuscribirse de eventos
  const off = (event, callback) => {
    if (socketRef.current) {
      socketRef.current.off(event, callback);
    }
  };

  return {
    socket: socketRef.current,
    isConnected,
    syncStatus,
    on,
    off
  };
}
