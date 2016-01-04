import {expect} from 'chai';
import nock from 'nock';

import SETTINGS from '../src/settings';
import Request from '../src/request';

describe('request', () => {
  it("sends a GET request", () => {
    const expectedResponse = {
      success: true
    }

    nock(SETTINGS.API_BASE)
      .get('/')
      .reply(200, expectedResponse)

    let result;

    Request.get('/',
      (json => {
        expect(json).to.deep.equal(expectedResponse)
      })
    );
  });

  it("processes an empty response", () => {
    const expectedResponse = {}

    nock(SETTINGS.API_BASE)
      .get('/')
      .reply(200, null)

    let result;

    Request.get('/',
      (json => {
        expect(json).to.deep.equal(expectedResponse)
      })
    );
  });

  it("sends a POST request", () => {
    const expectedResponse = {
      success: true
    }

    nock(SETTINGS.API_BASE)
      .post('/', {})
      .reply(200, expectedResponse)

    let result;

    Request.post('/',
      (json => {
        expect(json).to.deep.equal(expectedResponse)
      }),
      {}
    );
  });

  it("sends a PUT request", () => {
    const expectedResponse = {
      success: true
    }

    nock(SETTINGS.API_BASE)
      .put('/', {})
      .reply(200, expectedResponse)

    let result;

    Request.put('/',
      (json => {
        expect(json).to.deep.equal(expectedResponse)
      }),
      {}
    );
  });

  it("sends a PATCH request", () => {
    const expectedResponse = {
      success: true
    }

    nock(SETTINGS.API_BASE)
      .patch('/', {})
      .reply(200, expectedResponse)

    let result;

    Request.patch('/',
      (json => {
        expect(json).to.deep.equal(expectedResponse)
      }),
      {}
    );
  });

  it("sends a DELETE request", () => {
    nock(SETTINGS.API_BASE)
      .delete('/')
      .reply(204)

    let result;

    Request.delete('/',
      (json => {
        expect(json).to.deep.equal({})
      })
    );
  });
})