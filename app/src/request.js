import fetch from 'isomorphic-fetch';
import { polyfill } from 'es6-promise'; polyfill();

import SETTINGS from './settings';

function request(url, method, callback, body={}, authenticate=true) {
  let fetchParams = {
    method: method,
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
  };

  if (authenticate) {
    fetchParams.headers.Authorization = 'Token ' + window.localStorage.auth_token
  }

  if (body) {
    fetchParams.body = JSON.stringify(body)
  }

  return fetch(SETTINGS.API_BASE + url, fetchParams)
    .then(response => {
      if (response.status >= 400) {
        response.json().then(error => {
          callback({
            success: false,
            content: response
          })
        })
      } else {
        response.text().then(response => {
          callback({
            success: true,
            content: JSON.parse(response || '{}')
          })
        })
      }
    });
}

const Request = {
  get: function(url, callback, authenticate) {
    return request(url, 'GET', callback, null, authenticate);
  },

  delete: function(url, callback, authenticate) {
    return request(url, 'DELETE', callback, null, authenticate);
  },

  post: function(url, callback, body, authenticate) {
    return request(url, 'POST', callback, body, authenticate);
  },

  put: function(url, callback, body, authenticate) {
    return request(url, 'PUT', callback, body, authenticate);
  },

  patch: function(url, callback, body, authenticate) {
    return request(url, 'PATCH', callback, body, authenticate);
  }
}

export default Request;