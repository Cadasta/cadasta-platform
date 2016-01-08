export default class Storage {
  constructor(height, width) {
    this.storage = {};
  }

  setItem(key, value) {
    this.storage[key] = value || '';
  }

  getItem(key) {
    return this.storage[key] || null;
  }

  removeItem(key) {
    delete this.storage[key];
  }
}
