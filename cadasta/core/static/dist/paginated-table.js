var _extends = Object.assign || function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; };

class PaginatedTable extends React.Component {

  // TODO: Set default and req'd props
  constructor(props) {
    super(props);
    this.state = {
      data: [],
      loading: null,
      err: null,

      limit: Number(this.getParameterByName('limit')) || props.limit,
      offset: Number(this.getParameterByName('offset')) || 0,
      search: this.getParameterByName('search') || '',
      ordering: this.getParameterByName('ordering') || '',

      count: 0,
      query: props.query || {}
    };
  }

  componentDidMount() {
    this.fetchData();
  }

  /**
   * Event handler to increment/decrement page of paginated data. Runs
   * fetchData() after value is set.
   * @param  {SyntheticEvent} event Event generated via onClick
   * @param  {Number} direction     Increment value for page (i.e. -1 for last page, 1 for next page)
   * @return {null}
   */
  changePage(event, direction) {
    this.setState(previousState => {
      let change = direction * previousState.limit;
      return {
        offset: Math.max(previousState.offset + change, 0)
      };
    }, () => this.fetchData());
  }

  /**
   * Event handler to alter number of elements per page of paginated data. Runs
   * fetchData() after value is set.
   * @param  {SyntheticEvent} event     Event generated via onClick
   * @return {null}
   */
  changeLimit(event) {
    const limit = Number(event.target.value);
    this.setState(prevState => {
      // Adjust offset so that it starts at an interval of the new limit
      // (i.e. if we were looking at third page of data, it will still show
      // third page of data with new values)
      let offset = Math.floor(prevState.offset / prevState.limit) * limit;
      // If new limit makes current page empty, set values so that view is
      // of last page that would contain data
      if (offset >= prevState.count) {
        offset = (Math.ceil(prevState.count / limit) - 1) * limit;
      }
      return { limit, offset };
    }, () => this.fetchData(false));
  }

  /**
   * Set search query for API. Runs fetchData() after value is set.
   * @param  {String} value Query string
   * @return {null}
   */
  changeSearch(value) {
    this.setState({ search: value }, () => this.fetchData(false));
  }

  /**
   * Set ordering value for API.
   * @param  {String} orderName Order value. Prepend with '-' for descending
   *                            order.
   * @return {null}
   */
  changeOrder(orderName) {
    let newOrder = orderName;
    if (newOrder == this.state.ordering) {
      newOrder = newOrder.startsWith('-') ? newOrder.subString(1) : '-' + newOrder;
    }
    this.setState({ ordering: newOrder }, () => this.fetchData(false));
  }

  /**
   * Transforms an object of parameters into a querystring that can be appended
   * to a URL.
   * @param  {Object} params Object representing querystring GET parameters
   * @return {String}        GET param querystring
   */
  getQueryString(params) {
    var esc = encodeURIComponent;
    return Object.keys(params).map(k => esc(k) + '=' + esc(params[k])).join('&');
  }

  /**
   * Retrieve value from window's URL's GET parameters.
   * @param  {String} name  Name of URL parameter to retrieve
   * @return {String/null}  URL paramenter value (as string) if present, null
   *                        otherwise
   */
  getParameterByName(name) {
    var match = RegExp('[?&]' + name + '=([^&]*)').exec(window.location.search);
    return match && decodeURIComponent(match[1].replace(/\+/g, ' '));
  }

  /**
   * Retrieve data from API with component state's settings.
   * @param  {Boolean} [loading=true] Whether table should clear and show
   *                                  "loading" message while request is
   *                                  in-flight.
   * @return {null}
   */
  fetchData(loading = true) {
    // TODO: This may be a good place to set params in URL
    this.setState({ loading, err: null });
    this.setUrl();

    const urlProps = {
      limit: this.state.limit,
      offset: this.state.offset,
      search: this.state.search,
      ordering: this.state.ordering
    };
    const apiQueryObj = Object.assign(urlProps, this.state.query);
    const query = this.getQueryString(apiQueryObj);
    const apiUrl = `${this.props.url}?${query}`;

    fetch(apiUrl, {
      credentials: "same-origin"
    }).catch(err => {
      this.setState({
        loading: false,
        err: true
      });
    }).then(result => result.json()).then(data => {
      this.setState({
        data: data['results'],
        loading: false,
        count: data['count']
      });
    });
  }

  /**
   * Set window's URL query parameters to match aspects of component's state
   */
  setUrl() {
    const urlProps = {
      limit: this.state.limit,
      offset: this.state.offset,
      search: this.state.search,
      ordering: this.state.ordering
      // Remove empty strings and null values from urlProps object
    };Object.keys(urlProps).forEach(key => !urlProps[key] && delete urlProps[key]);
    const getParams = this.getQueryString(urlProps);
    const url = `${window.location.pathname}?${getParams}`;
    window.history.replaceState(null, null, url);
  }

  /**
   * Generate table body based on component's state.
   * @return {Element} table body
   */
  renderTableBody() {
    if (this.state.loading || this.state.err) {
      return React.createElement(
        'td',
        { colSpan: '100%', style: { "text-align": "center", padding: "10px" } },
        this.state.loading ? "Loading..." : "Error fetching data"
      );
    }
    if (!this.state.data.length) {
      return React.createElement(
        'td',
        { colSpan: '100%', style: { "text-align": "left", padding: "10px" } },
        'No data available in table'
      );
    }
    return this.state.data.map(obj => React.createElement(Row, {
      data: obj,
      layouts: this.props.layouts,
      getLink: this.props.rowLink
    }));
  }

  render() {
    return React.createElement(
      'div',
      { className: 'dataTables_wrapper form-inline dt-bootstrap no-footer' },
      React.createElement(SearchField, {
        query: this.state.search,
        handleSearch: this.changeSearch.bind(this) }),
      React.createElement(
        'table',
        { id: 'DataTables_Table_0', className: 'table table-hover dataTable' },
        React.createElement(
          'thead',
          null,
          React.createElement(
            'tr',
            null,
            this.props.layouts.map(layout => React.createElement(Header, _extends({
              ordering: this.state.ordering,
              setOrder: this.changeOrder.bind(this),
              thClasses: this.props.thClasses
            }, layout)))
          )
        ),
        React.createElement(
          'tbody',
          null,
          this.renderTableBody()
        )
      ),
      React.createElement(PaginationNav, {
        onChange: this.changePage.bind(this),
        showNext: this.state.limit + this.state.offset < this.state.count,
        showPrev: this.state.offset > 0
      }),
      React.createElement(PaginationInfo, {
        offset: this.state.offset,
        count: this.state.count,
        length: this.state.data.length
      }),
      React.createElement(PerPageDropdown, {
        value: this.state.limit,
        onChange: this.changeLimit.bind(this)
      })
    );
  }
}

PaginatedTable.propTypes = {
  url: PropTypes.string.isRequired,
  layouts: PropTypes.arrayOf(PropTypes.shape({
    render: PropTypes.func.isRequired,
    title: PropTypes.string,
    columns: PropTypes.number,
    orderKeyword: PropTypes.string
  }).isRequired).isRequired,

  thClasses: PropTypes.string,
  limit: PropTypes.number,
  query: PropTypes.object,
  rowLink: PropTypes.func
};
PaginatedTable.defaultProps = {
  limit: 10
};

const Header = ({ orderKeyword, ordering, columns, setOrder, title, thClasses }) => {

  /**
   * Set ordering class based on properties. Class controls iconography after
   * header name.
   * @param  {string} keyword  Ordering keyword for particuler header
   * @param  {string} ordering Current ordering value
   * @return {string}          Class name
   */
  const getOrderingClass = (keyword, ordering) => {
    if (!keyword || !ordering) return '';
    if (orderKeyword == ordering) return 'sorting_asc';
    if (orderKeyword == ordering.slice(1)) return 'sorting_desc';
    return '';
  };
  return React.createElement(
    'th',
    {
      className: `col-md-${columns} ` + thClasses + ' ' + getOrderingClass(orderKeyword, ordering),
      style: orderKeyword ? { cursor: 'pointer' } : {},
      onClick: orderKeyword ? () => setOrder(orderKeyword) : null
    },
    title
  );
};
Header.defaultProps = {
  columns: 1
};

const Row = ({ getLink, data, layouts }) => React.createElement(
  'tr',
  {
    style: getLink ? { cursor: 'pointer' } : {},
    onClick: getLink ? () => {
      window.location = getLink(data);
    } : null,
    'data-link-url': getLink ? getLink(data) : null
  },
  layouts.map(layout => layout.render(data))
);

class SearchField extends React.Component {
  // https://stackoverflow.com/questions/23123138/perform-debounce-in-react-js/24679479#24679479
  constructor(props) {
    super(props);
    this.state = {
      query: props.query
    };
  }

  /**
   * Prevent excessive calls to wrapped function.
   * @param  {Function} func    Function to be debounced
   * @param  {Number}   wait    Wait time (in milliseconds) for debounce
   * @param  {Boolean}  immediate Whether function should allow initial call
   *                              through immediately.
   * @return {null}
   */
  debounce(func, wait, immediate) {
    // http://davidwalsh.name/javascript-debounce-function
    var timeout;
    return function () {
      var context = this,
          args = arguments;
      var later = function () {
        timeout = null;
        if (!immediate) func.apply(context, args);
      };
      var callNow = immediate && !timeout;
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
      if (callNow) func.apply(context, args);
    };
  }

  componentWillMount() {
    this.handleSearchDebounced = this.debounce(function () {
      this.props.handleSearch.apply(this, [this.state.query]);
    }, 500);
  }

  onChange() {
    this.setState({ query: this.refs.searchBox.value });
    this.handleSearchDebounced();
  }

  render() {
    return React.createElement(
      'div',
      { className: 'table-search clearfix' },
      React.createElement(
        'div',
        { id: 'DataTables_Table_0_filter', className: 'dataTables_filter' },
        React.createElement(
          'label',
          null,
          React.createElement(
            'div',
            { className: 'input-group' },
            React.createElement(
              'span',
              { className: 'input-group-addon' },
              React.createElement('span', { className: 'glyphicon glyphicon-search' })
            ),
            React.createElement('input', { type: 'search',
              className: 'form-control input-sm',
              placeholder: 'Search',
              'aria-controls': 'paginated-table',
              ref: 'searchBox',
              value: this.state.query,
              onChange: this.onChange.bind(this) })
          )
        )
      )
    );
  }
}

function PaginationNav({ showNext, showPrev, onChange }) {
  return React.createElement(
    'div',
    { className: 'table-pagination' },
    React.createElement(
      'div',
      { className: 'dataTables_paginate paging_simple' },
      React.createElement(
        'ul',
        { className: 'pagination' },
        React.createElement(
          'li',
          {
            className: `paginate_button previous ${!showPrev && "disabled"}`,
            onClick: e => showPrev && onChange(e, -1)
          },
          React.createElement(
            'a',
            { href: '', 'aria-controls': 'paginated-table', tabindex: '0', onClick: e => e.preventDefault() },
            React.createElement('span', { className: 'glyphicon glyphicon-triangle-left' })
          )
        ),
        React.createElement(
          'li',
          {
            className: `paginate_button next ${!showNext && "disabled"}`,
            onClick: e => showNext && onChange(e, 1)
          },
          React.createElement(
            'a',
            { href: '', 'aria-controls': 'paginated-table', tabindex: '0', onClick: e => e.preventDefault() },
            React.createElement('span', { className: 'glyphicon glyphicon-triangle-right' })
          )
        )
      )
    )
  );
}

function PaginationInfo({ length, offset, count }) {
  return React.createElement(
    'div',
    { className: 'table-entries' },
    React.createElement(
      'div',
      { className: 'dataTables_info', role: 'status', 'aria-live': 'polite' },
      'Showing ',
      offset + 1,
      ' - ',
      length ? offset + length : offset + 1,
      ' of ',
      count
    )
  );
}

function PerPageDropdown({ value, onChange }) {
  return React.createElement(
    'div',
    { className: 'table-num' },
    React.createElement(
      'div',
      { className: 'dataTables_length' },
      React.createElement(
        'label',
        null,
        React.createElement(
          'select',
          {
            className: 'form-control input-sm',
            value: value,
            onChange: onChange
          },
          React.createElement(
            'option',
            { value: '10' },
            '10 per page'
          ),
          React.createElement(
            'option',
            { value: '25' },
            '25 per page'
          ),
          React.createElement(
            'option',
            { value: '50' },
            '50 per page'
          ),
          React.createElement(
            'option',
            { value: '100' },
            '100 per page'
          )
        )
      )
    )
  );
}