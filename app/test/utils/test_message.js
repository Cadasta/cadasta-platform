import { expect } from 'chai';
import { fromJS } from 'immutable';

import { createMessage } from '../../src/utils/messages';

describe("utils.messages.parseError", () => {
  it("creates message without detail", () => {
    const result = createMessage('error', "Message");

    expect(result).to.deep.equal(fromJS({
      type: 'error',
      msg: "Message"
    }));
  });

  it("creates message with detail", () => {
    const response = {
      "email": ["Another user is already registered with this email address"],
      "username":["A user with that username already exists."]
    };
    const result = createMessage('error', "Message", response);

    expect(result).to.deep.equal(fromJS({
      type: 'error',
      msg: "Message",
      details: [
        "Another user is already registered with this email address",
        "A user with that username already exists."
      ]
    }));
  });

  it("creates network error message", () => {
    const response = {
      "network_error": "Unable to connect to the server."
    };

    const result = createMessage('error', "Message", response);

    expect(result).to.deep.equal(fromJS({
      type: 'error',
      msg: "Unable to connect to the server."
    }));
  });
});
