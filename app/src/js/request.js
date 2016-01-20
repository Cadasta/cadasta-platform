import { Promise } from 'es6-promise';

import SETTINGS from './settings';

function request(url, method, body = {}, authenticate = true) {
  const promise = new Promise(function promise(resolve, reject) {
    const client = new XMLHttpRequest();

    client.open(method, SETTINGS.API_BASE + url, true);

    client.setRequestHeader('Accept', 'application/json');
    client.setRequestHeader('Content-Type', 'application/json');

    if (authenticate) {
      client.setRequestHeader('Authorization', 'Token ' + window.sessionStorage.auth_token);
    }

    client.send(JSON.stringify(body));

    client.onload = function onload() {
      let response;
      if (this.response) {
        response = JSON.parse(this.response);
      }

      if (this.status >= 200 && this.status < 300) {
        resolve(response);
      } else {
        reject(response);
      }
    };

    client.onerror = function onerror() {
      reject({ network_error: 'Unable to connect to the server.' });
    };
  });
  return promise;
}

const Request = {
  get: function get(url, authenticate) {
    return request(url, 'GET', null, authenticate);
  },

  delete: function del(url, authenticate) {
    return request(url, 'DELETE', null, authenticate);
  },

  post: function post(url, body, authenticate) {
    return request(url, 'POST', body, authenticate);
  },

  put: function put(url, body, authenticate) {
    return request(url, 'PUT', body, authenticate);
  },

  patch: function patch(url, body, authenticate) {
    return request(url, 'PATCH', body, authenticate);
  },
};

export default Request;
