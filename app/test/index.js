const testsContext = require.context('.', true, /test_[(a-z|_)]*\.js$/);
testsContext.keys().forEach(testsContext);
