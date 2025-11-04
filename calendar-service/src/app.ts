import express, { Request, Response } from 'express';
import taskRoutes from './routes/calendar';
import locationRoutes from './routes/location';

const app = express();
const port = process.env.PORT || 3000;

app.use(express.json());
app.use('/calendar', taskRoutes);
app.use('/location', locationRoutes);

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
