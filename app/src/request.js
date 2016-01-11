import { Promise } from 'es6-promise';

import SETTINGS from './settings';

function request(url, method, body={}, authenticate=true) {
  const promise = new Promise(function(resolve, reject) {
    const client = new XMLHttpRequest();

    client.open(method, SETTINGS.API_BASE + url, true);

    client.setRequestHeader('Accept', 'application/json');
    client.setRequestHeader('Content-Type', 'application/json');

    if (authenticate) {
      client.setRequestHeader('Authorization', 'Token ' + window.localStorage.auth_token);
    }

    client.send(JSON.stringify(body));

    client.onload = function () {
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

    client.onerror = function () {
      reject(this.statusText);
    };
  });
  return promise;
}

const Request = {
  get: function(url, authenticate) {
    return request(url, 'GET', null, authenticate);
  },

  delete: function(url, authenticate) {
    return request(url, 'DELETE', null, authenticate);
  },

  post: function(url, body, authenticate) {
    return request(url, 'POST', body, authenticate);
  },

  put: function(url, body, authenticate) {
    return request(url, 'PUT', body, authenticate);
  },

  patch: function(url, body, authenticate) {
    return request(url, 'PATCH', body, authenticate);
  }
}

export default Request;