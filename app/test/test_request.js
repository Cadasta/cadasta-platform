import {expect} from 'chai';
import nock from 'nock';

import SETTINGS from '../src/settings';
import Request from '../src/request';

describe('request', () => {
  it("sends a GET request", () => {
    const response = { some: "Response" }
    const expectedResponse = {
      success: true,
      content: response
    }

    nock(SETTINGS.API_BASE)
      .get('/')
      .reply(200, response)

    return Request.get(
      '/',
      (json => expect(json).to.deep.equal(expectedResponse))
    );
  });

  it("handles HTTP errors", () => {
    const response = { some: "Error" }
    const expectedResponse = {
      success: false,
      content: response
    }

    nock(SETTINGS.API_BASE)
      .get('/')
      .reply(400, response)

    return Request.get('/',
      (json => {
        expect(json).to.deep.equal(expectedResponse)
      })
    );
  });

  it("processes an empty response", () => {
    const expectedResponse = {
      success: true,
      content: {}
    }

    nock(SETTINGS.API_BASE)
      .get('/')
      .reply(200, null)

    return Request.get('/',
      (json => {
        expect(json).to.deep.equal(expectedResponse)
      })
    );
  });

  it("sends a POST request", () => {
    const response = { some: "Response" }
    const expectedResponse = {
      success: true,
      content: response
    }

    nock(SETTINGS.API_BASE)
      .post('/', {})
      .reply(200, response)

    return Request.post('/',
      (json => {
        expect(json).to.deep.equal(expectedResponse)
      }),
      {}
    );
  });

  it("sends a PUT request", () => {
    const response = { some: "Response" }
    const expectedResponse = {
      success: true,
      content: response
    }

    nock(SETTINGS.API_BASE)
      .put('/', {})
      .reply(200, response)

    return Request.put('/',
      (json => {
        expect(json).to.deep.equal(expectedResponse)
      }),
      {}
    );
  });

  it("sends a PATCH request", () => {
    const response = { some: "Response" }
    const expectedResponse = {
      success: true,
      content: response
    }

    nock(SETTINGS.API_BASE)
      .patch('/', {})
      .reply(200, response)

    return Request.patch('/',
      (json => {
        expect(json).to.deep.equal(expectedResponse)
      }),
      {}
    );
  });

  it("sends a DELETE request", () => {
    const expectedResponse = {
      success: true,
      content: {}
    }

    nock(SETTINGS.API_BASE)
      .delete('/')
      .reply(204)

    return Request.delete('/',
      (json => {
        expect(json).to.deep.equal(expectedResponse)
      })
    );
  });
});
