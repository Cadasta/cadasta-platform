export const REQUEST_START = 'REQUEST_START';
export const REQUEST_DONE = 'REQUEST_DONE';

export const DISMISS_MESSAGES = 'DISMISS_MESSAGES';

export function requestStart() {
  return { type: REQUEST_START }
}

export function requestDone() {
  return { type: REQUEST_DONE }
}

export function dismissMessages() {
  return { type: DISMISS_MESSAGES }	
}