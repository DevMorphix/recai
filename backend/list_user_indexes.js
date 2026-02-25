// Run this script with: node list_user_indexes.js
require('dotenv').config();
const mongoose = require('mongoose');

async function listIndexes() {
  await mongoose.connect(process.env.MONGODB_URI);
  const indexes = await mongoose.connection.db.collection('users').indexes();
  const fs = require('fs');
  fs.writeFileSync('user_indexes.json', JSON.stringify(indexes, null, 2));
  console.log('Indexes written to user_indexes.json');
  await mongoose.disconnect();
}

listIndexes().then(() => process.exit(0)).catch(e => { console.error(e); process.exit(1); });
