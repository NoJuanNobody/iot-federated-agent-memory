import OpenAI from 'openai';
import type { Config } from './config.js';

/**
 * OpenRouter exposes an OpenAI-compatible API, so the official OpenAI SDK
 * pointed at openrouter.ai gives us streaming + function calling across
 * every model it serves. The extra headers are OpenRouter's optional
 * app-attribution convention.
 */
export function createClient(config: Pick<Config, 'apiKey' | 'baseURL'>): OpenAI {
  return new OpenAI({
    apiKey: config.apiKey,
    baseURL: config.baseURL,
    defaultHeaders: {
      'HTTP-Referer': 'https://github.com/NoJuanNobody/dsx',
      'X-Title': 'dsx',
    },
  });
}
