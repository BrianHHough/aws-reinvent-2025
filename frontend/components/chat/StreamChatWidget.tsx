'use client';

import { useEffect, useState } from 'react';
import {
  Chat,
  Channel,
  ChannelHeader,
  MessageInput,
  MessageList,
  Thread,
  Window,
  useCreateChatClient,
} from 'stream-chat-react';
import type { Channel as StreamChannel, UserResponse } from 'stream-chat';
import { MessageCircle, X, Sparkles } from 'lucide-react';
import CustomChannelHeader from './ChannelHeader';

const FASTAPI_URL =
  process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://127.0.0.1:8000';

// 🎯 SPOTLIGHT MODE: Set to true to add a dark overlay behind the chatbot
const SPOTLIGHT_MODE = false;

type StreamConfig = {
  apiKey: string;
  token: string;
  user: UserResponse;
};

// Custom empty state component
const CustomEmptyState = () => (
  <div className="flex flex-col items-center justify-center h-full p-8 text-center">
    <div className="bg-blue-100 rounded-full p-4 mb-4">
      <Sparkles className="w-8 h-8 text-blue-600" />
    </div>
    <h3 className="text-lg font-semibold text-gray-900 mb-2">
      Welcome to FinStack AI
    </h3>
    <p className="text-sm text-gray-600 max-w-xs">
      Start a conversation with our AI assistant. Ask about pricing, features, or anything else!
    </p>
  </div>
);

/**
 * Outer wrapper:
 * - talks to FastAPI
 * - shows loading/error
 * - only renders inner widget once config is ready
 */
export default function StreamChatWidget() {
  const [config, setConfig] = useState<StreamConfig | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  // In a real app you'd get these from your auth/session
  const userId = 'demo_user_1';
  const userName = 'Demo User';

  useEffect(() => {
    const fetchToken = async () => {
      try {
        setError(null);

        const res = await fetch(`${FASTAPI_URL}/stream/token`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: userId,
            name: userName,
          }),
        });

        if (!res.ok) {
          throw new Error(`Token endpoint failed: ${res.status}`);
        }

        const data = await res.json();

        setConfig({
          apiKey: data.api_key,
          token: data.token,
          user: data.user,
        });
      } catch (err) {
        console.error(err);
        if (err instanceof Error) {
            setError(err.message);
        } else {
            setError('Failed to load chat config');
        }
      }
    };

    fetchToken();
  }, [userId, userName]);

  const handleClearChat = async () => {
    if (!config) return;
    
    try {
      // Call backend to delete all messages
      const userId = config.user.id as string;
      await fetch(`${FASTAPI_URL}/stream/clear-chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId }),
      });
      
      // Force refresh by toggling open state
      setIsOpen(false);
      setTimeout(() => setIsOpen(true), 100);
    } catch (err) {
      console.error('Failed to clear chat:', err);
    }
  };

  return (
    <>
      {/* Spotlight Mode Overlay */}
      {SPOTLIGHT_MODE && isOpen && (
        <div
          className="fixed inset-0 z-40 transition-opacity duration-300"
          style={{ backgroundColor: 'rgba(0, 0, 0, 0.8)' }}
          onClick={() => setIsOpen(false)}
          aria-label="Close chat overlay"
        />
      )}

      {/* Floating Chat Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg flex items-center justify-center transition-all duration-200 hover:scale-110 z-50"
        aria-label="Toggle chat"
      >
        {isOpen ? <X className="w-6 h-6" /> : <MessageCircle className="w-6 h-6" />}
      </button>

      {/* Chat Panel */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-96 h-[600px] bg-white rounded-lg shadow-2xl border border-gray-200 overflow-hidden z-50 flex flex-col">
          {error ? (
            <div className="flex items-center justify-center h-full p-4 text-center">
              <div>
                <p className="text-red-600 font-semibold mb-2">Chat Error</p>
                <p className="text-sm text-gray-600">{error}</p>
              </div>
            </div>
          ) : !config ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                <p className="text-sm text-gray-600">Connecting chat…</p>
              </div>
            </div>
          ) : (
            <>
            <InnerChatWidget config={config} />
            <button
                onClick={handleClearChat}
                className="absolute top-4 right-4 text-gray-500 hover:text-red-600 text-xs px-2 py-1 rounded hover:bg-gray-100 transition"
                title="Clear chat history"
              >
                Clear
              </button>
              </>
          )}
        </div>
      )}
    </>
  );
}

/**
 * Inner widget:
 * - assumes config is non-null
 * - safe to call useCreateChatClient with required object
 */
function InnerChatWidget({ config }: { config: StreamConfig }) {
  const [activeChannel, setActiveChannel] = useState<StreamChannel | null>(null);
  
  const client = useCreateChatClient({
    apiKey: config.apiKey,
    tokenOrProvider: config.token,
    userData: config.user,
  });

  const userId = config.user.id as string;

  useEffect(() => {
    if (!client) return;

    const initChannel = async () => {
      try {
        // Create or get a support channel for this user
        const channel = client.channel('messaging', `support-${userId}`, {
          members: [userId],
        });

        await channel.watch();
        setActiveChannel(channel);
      } catch (error) {
        console.error('Error initializing channel:', error);
      }
    };

    initChannel();
  }, [client, userId]);

  if (!client || !activeChannel) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
          <p className="text-sm text-gray-600">Connecting chat…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <Chat client={client}>
        <Channel channel={activeChannel} EmptyStateIndicator={CustomEmptyState}>
          <Window>
            <CustomChannelHeader />
            <MessageList />
            <MessageInput maxRows={6} />
          </Window>
          <Thread />
        </Channel>
      </Chat>
    </div>
  );
}