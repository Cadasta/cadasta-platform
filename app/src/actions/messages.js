export const MESSAGE_DISMISS = 'MESSAGE_DISMISS';

export function messageDismiss(messageId) {
  return {
    type: MESSAGE_DISMISS,
    messageId
  }
}