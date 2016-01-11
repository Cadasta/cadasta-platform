import { fromJS } from 'immutable';


function parseError(response) {
  let errorList = [];

  for (var key in response) {
    errorList = errorList.concat(response[key]);
  }

  return errorList;
}

export function createMessage(type, msg, response) {
  var message = { type, msg };

  if (response) {
  	if (response.network_error) {
      message.msg = response.network_error;
  	} else {
  	  message.details = parseError(response);
  	}
  }

  return fromJS(message);
}