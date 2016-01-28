export const ROUTER_REDIRECT = 'ROUTER_REDIRECT';

export function redirect(redirectTo) {
  return {
    type: ROUTER_REDIRECT,
    redirectTo,
    keepMessages: true,
  };
}
