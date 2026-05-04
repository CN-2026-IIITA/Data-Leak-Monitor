import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const { provider, apiKey, messages } = await req.json();

    if (!apiKey) {
      return NextResponse.json({ error: 'API Key is required. Please set it in Settings.' }, { status: 400 });
    }

    if (!messages || !Array.isArray(messages)) {
      return NextResponse.json({ error: 'Invalid messages array.' }, { status: 400 });
    }

    let responseContent = '';

    if (provider === 'openai') {
      const res = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`,
        },
        body: JSON.stringify({
          model: 'gpt-3.5-turbo',
          messages: messages,
        }),
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error.message || 'OpenAI API Error');
      responseContent = data.choices[0].message.content;

    } else if (provider === 'gemini') {
      const geminiMessages = messages.map(m => ({
        role: m.role === 'assistant' ? 'model' : 'user',
        parts: [{ text: m.content }]
      }));
      const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: geminiMessages,
        }),
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error.message || 'Gemini API Error');
      responseContent = data.candidates[0].content.parts[0].text;

    } else if (provider === 'claude') {
      // Claude requires alternating user/assistant roles.
      const claudeMessages = messages.filter(m => m.role !== 'system').map(m => ({
        role: m.role,
        content: m.content
      }));
      const systemMsg = messages.find(m => m.role === 'system')?.content || '';
      
      const res = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': apiKey,
          'anthropic-version': '2023-06-01'
        },
        body: JSON.stringify({
          model: 'claude-3-haiku-20240307',
          max_tokens: 1000,
          system: systemMsg,
          messages: claudeMessages,
        }),
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error.message || 'Claude API Error');
      responseContent = data.content[0].text;
    } else {
      throw new Error('Unsupported provider');
    }

    return NextResponse.json({ reply: responseContent });

  } catch (error: any) {
    console.error('AI Chat Error:', error);
    return NextResponse.json({ error: error.message || 'An error occurred during AI generation' }, { status: 500 });
  }
}
