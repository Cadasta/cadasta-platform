import { expect } from 'chai';

import { parseError } from '../../src/utils/messages';

describe("utils.parseError", () => {
  it("parse registration response", () => {
    const response = {
      "email": ["Another user is already registered with this email address"],
      "username":["A user with that username already exists."]
    };

    const result = parseError(response);

    expect(result).to.deep.equal([
      "Another user is already registered with this email address",
      "A user with that username already exists."
    ]);
  });
});
