import {expect} from 'chai';
import * as messageActions from '../../src/actions/messages';

describe('Actions: Messages', () => {
  it ('creates REQUEST_START', () => {
    const action = messageActions.requestStart();

    expect(action).to.deep.equal({
      type: messageActions.REQUEST_START,
    })
  });

  it ('creates REQUEST_DONE', () => {
    const action = messageActions.requestDone();

    expect(action).to.deep.equal({
      type: messageActions.REQUEST_DONE,
    })
  });
});