import fetch from 'isomorphic-fetch';

import SETTINGS from './settings';

function request(url, method, successCallback, body={}, authenticate=true) {
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
    .then(response => response.text())
    .then(text => JSON.parse(text || '{}'))
    .then(successCallback);
}

const Request = {
  get: function(url, successCallback, authenticate) {
    return request(url, 'GET', successCallback, null, authenticate);
  },

  delete: function(url, successCallback, authenticate) {
    return request(url, 'DELETE', successCallback, null, authenticate);
  },

  post: function(url, successCallback, body, authenticate) {
    return request(url, 'POST', successCallback, body, authenticate);
  },

  put: function(url, successCallback, body, authenticate) {
    return request(url, 'PUT', successCallback, body, authenticate);
  },

  patch: function(url, successCallback, body, authenticate) {
    return request(url, 'PATCH', successCallback, body, authenticate);
  }
}

export default Request;