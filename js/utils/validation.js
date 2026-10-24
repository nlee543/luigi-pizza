export function checkoutErrors(data) {
  const errors = {};
  for (const key of ['firstName', 'lastName', 'phone', 'email'])
    if (!String(data[key] || '').trim()) errors[key] = 'This field is required.';
  if (data.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email))
    errors.email = 'Enter a valid email address.';
  if (
    (data.phone && !/^\+?[\d ()-]{10,20}$/.test(data.phone)) ||
    (data.phone && data.phone.replace(/\D/g, '').length < 10)
  )
    errors.phone = 'Enter a phone number with at least 10 digits.';
  if (data.type === 'delivery') {
    for (const key of ['street', 'city', 'state', 'zip'])
      if (!String(data[key] || '').trim()) errors[key] = 'Required for delivery.';
    if (data.state && !/^[A-Za-z]{2}$/.test(data.state))
      errors.state = 'Use a two-letter state abbreviation.';
    if (data.zip && !/^\d{5}(-\d{4})?$/.test(data.zip)) errors.zip = 'Enter a valid ZIP code.';
  }
  if (!['pickup', 'delivery'].includes(data.type)) errors.type = 'Choose pickup or delivery.';
  if (!['demo', 'store'].includes(data.payment)) errors.payment = 'Choose a payment option.';
  return errors;
}
