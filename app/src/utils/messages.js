export function parseError(response) {
  let errorList = [];

  for (var key in response) {
    errorList = errorList.concat(response[key]);
  }

  return errorList;
}