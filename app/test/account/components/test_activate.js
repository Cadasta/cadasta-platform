import React from 'react/addons';
import TestUtils from 'react-addons-test-utils';

import { Activate } from '../../../src/js/account/components/Activate';

describe('Account: Components: Activate', () => {
  it('invokes callback when mounted', () => {
    const accountActivate = (tokens) => {
      expect(tokens).to.deep.equal({
        uid: 'MQ',
        token: '489-963055ee7742ad6c4440',
      });
    };

    const params = {
      uid: 'MQ',
      token: '489-963055ee7742ad6c4440',
    };

    TestUtils.renderIntoDocument(<Activate params={params} accountActivate={accountActivate} />);
  });
});
