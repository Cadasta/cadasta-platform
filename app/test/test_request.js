import chai, {expect, assert} from 'chai';
import nock from 'nock';

import SETTINGS from '../src/settings';
import Request from '../src/request';

describe('request', () => {
  it("sends a GET request", () => {
    const response = { some: "Response" }

    nock(SETTINGS.API_BASE)
      .get('/')
      .reply(200, response)

    return Request.get('/')
      .then(
        (success => expect(success).to.deep.equal(response)),
        (error => assert(false, "Error called with: " + JSON.stringify(error)))
      )
  });

  it("handles HTTP errors", () => {
    const response = { some: "Error" }

    nock(SETTINGS.API_BASE)
      .get('/')
      .reply(400, response)

    return Request.get('/')
      .then(
        (success => assert(false, "Success called with: " + JSON.stringify(success))),
        (error => expect(error).to.deep.equal(response))
      )
  });

  it("throws an error when the network fails", () => {
    const response = { network_error: "Unable to connect to the server." }

    return Request.get('/')
      .then(
        (success => assert(false, "Success called with: " + JSON.stringify(error))),
        (error => expect(error).to.deep.equal(response))
      )
  });

  it("sends a POST request", () => {
    const response = { some: "Response" }

    nock(SETTINGS.API_BASE)
      .post('/', {})
      .reply(200, response)

    return Request.post('/', {})
      .then(
        (json => expect(json).to.deep.equal(response)),
        (error => assert(false, "Error called with: " + JSON.stringify(error)))
      );
  });

  it("sends a PUT request", () => {
    const response = { some: "Response" }

    nock(SETTINGS.API_BASE)
      .put('/', {})
      .reply(200, response)

    return Request.put('/', {})
      .then(
        (json => expect(json).to.deep.equal(response)),
        (error => assert(false, "Error called with: " + JSON.stringify(error)))
      );
  });

  it("sends a PATCH request", () => {
    const response = { some: "Response" }

    nock(SETTINGS.API_BASE)
      .patch('/', {})
      .reply(200, response)

    return Request.patch('/', {})
      .then(
        (json => expect(json).to.deep.equal(response)),
        (error => assert(false, "Error called with: " + JSON.stringify(error)))
      );
  });

  it("sends a DELETE request", () => {
    nock(SETTINGS.API_BASE)
      .delete('/')
      .reply(204)

    return Request.delete('/')
      .then(
        (json => expect(json).to.be.undefined),
        (error => assert(false, "Error called with: " + JSON.stringify(error)))
      );
  });
});
