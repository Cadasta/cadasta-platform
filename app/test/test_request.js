import SETTINGS from '../src/js/settings';
import Request from '../src/js/request';

describe('request', () => {
  let server;

  beforeEach(() => {
    server = sinon.fakeServer.create();
    server.autoRespond = true;
  });

  afterEach(() => {
    server.restore();
  });

  it('sends a GET request', () => {
    const response = { some: 'Response' };

    server.respondWith('GET', SETTINGS.API_BASE + '/', JSON.stringify(response));

    return Request.get('/')
      .then(
        success => expect(success).to.deep.equal(response),
        error => assert(false, 'Error called with: ' + JSON.stringify(error))
      );
  });

  it('handles HTTP errors', () => {
    const response = { some: 'Error' };

    server.respondWith('GET', SETTINGS.API_BASE + '/', [400, {}, JSON.stringify(response)]);

    return Request.get('/')
      .then(
        success => assert(false, 'Success called with: ' + JSON.stringify(success)),
        error => expect(error).to.deep.equal(response)
      );
  });

  it('throws an error when the network fails', () => {
    const response = { network_error: 'Unable to connect to the server.' };
    server.restore();

    return Request.get('/')
      .then(
        success => assert(false, 'Success called with: ' + JSON.stringify(success)),
        error => expect(error).to.deep.equal(response)
      );
  });

  it('sends a POST request', () => {
    const response = { some: 'Response' };

    server.respondWith('POST', SETTINGS.API_BASE + '/', JSON.stringify(response));

    return Request.post('/', {})
      .then(
        json => expect(json).to.deep.equal(response),
        error => assert(false, 'Error called with: ' + JSON.stringify(error))
      );
  });

  it('sends a PUT request', () => {
    const response = { some: 'Response' };

    server.respondWith('PUT', SETTINGS.API_BASE + '/', JSON.stringify(response));

    return Request.put('/', {})
      .then(
        json => expect(json).to.deep.equal(response),
        error => assert(false, 'Error called with: ' + JSON.stringify(error))
      );
  });

  it('sends a PATCH request', () => {
    const response = { some: 'Response' };

    server.respondWith('PATCH', SETTINGS.API_BASE + '/', JSON.stringify(response));

    return Request.patch('/', {})
      .then(
        json => expect(json).to.deep.equal(response),
        error => assert(false, 'Error called with: ' + JSON.stringify(error))
      );
  });

  it('sends a DELETE request', () => {
    server.respondWith('DELETE', SETTINGS.API_BASE + '/', [204, {}, '']);

    return Request.delete('/')
      .then(
        json => expect(json).to.be.undefined,
        error => assert(false, 'Error called with: ' + JSON.stringify(error))
      );
  });
});
