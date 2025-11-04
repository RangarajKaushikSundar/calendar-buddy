import { Router, Request, Response } from 'express';
import { CalendarEvent, Location } from '../types';
import { extractLocationFromResponse, setLocation } from './location';

const router = Router();
let calendarEvent: CalendarEvent[] = [];

// GET ALL
router.get('/get', (req: Request, res: Response) => {
  console.log(JSON.stringify(calendarEvent))
  res.json(calendarEvent);
});

router.get('/get/:id', (req: Request, res: Response) => {
  const event = calendarEvent.find((t) => t.id === req.params.id);
  if (!event) {
    res.status(404).send('Event not found');
  } else {
    res.json(event);
  }
});


// CREATE
router.post('/create', (req: Request, res: Response) => {
  const { title, startDatetime, endDatetime } = req.body;

  if (hasConflict(startDatetime, endDatetime)) {
    return res.status(409).json({ error: 'Event conflicts with an existing event' });
  }

  const location = extractLocationFromResponse(req);
  const event: CalendarEvent = {
    id: crypto.randomUUID(),
    title,
    startDatetime,
    endDatetime,
    location
  };

  setLocation(location);
  calendarEvent.push(event);
  res.status(201).json(event);
});


// UPDATE
router.post('/update/:id', (req: Request, res: Response) => {
  const event = calendarEvent.find((t) => t.id === req.params.id);
  if (!event) return res.status(404).send('Event not found');

  const newStart = req.body.startDatetime ?? event.startDatetime;
  const newEnd = req.body.endDatetime ?? event.endDatetime;

  if (hasConflict(newStart, newEnd, event.id)) {
    return res.status(409).json({ error: 'Event conflicts with an existing event' });
  }

  const location = extractLocationFromResponse(req);
  event.title = req.body.title || event.title;
  event.startDatetime = newStart;
  event.endDatetime = newEnd;
  event.location = req.body.location?.name ? location : event.location;

  res.json(event);
});


// DELETE
router.delete('/:id', (req: Request, res: Response) => {
  const index = calendarEvent.findIndex((t) => t.id === req.params.id);

  if (index === -1) {
    res.status(404).send('Event not found');
  } else {
    calendarEvent.splice(index, 1);
    res.status(204).send("Sucessfully deleted the event");
  }
});

// HELPERS

function hasConflict(startDatetime: number, endDatetime: number, excludeId?: string): boolean {
  return calendarEvent.some(event => {
    // Skip self when updating
    if (excludeId && event.id === excludeId) return false;

    const overlap = startDatetime < event.endDatetime && endDatetime > event.startDatetime;
    return overlap;
  });
}

export default router;