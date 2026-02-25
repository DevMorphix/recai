// Run this script with: node remove_phone_index.js
require('dotenv').config();
const mongoose = require('mongoose');

async function removePhoneIndex() {
  // Set your database name here if not 'test'
  const dbName = 'test'; // change if needed
  let uri = process.env.MONGODB_URI;
  if (!uri.endsWith(`/${dbName}`)) {
    uri = uri.endsWith('/') ? uri + dbName : uri + '/' + dbName;
  }
  await mongoose.connect(uri);
  const indexes = await mongoose.connection.db.collection('users').indexes();
  console.log('Current indexes:', indexes);
  try {
    const result = await mongoose.connection.db.collection('users').dropIndex('phone_1');
    console.log('Removed unique index on phone:', result);
  } catch (e) {
    console.error('Error removing index:', e.message);
  }
  await mongoose.disconnect();
}

removePhoneIndex().then(() => process.exit(0)).catch(e => { console.error(e); process.exit(1); });
