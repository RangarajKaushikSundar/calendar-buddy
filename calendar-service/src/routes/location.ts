import { Router, Request, Response } from 'express';
import { Location } from "../types";

const router = Router();

// TODO: Move to local storage or database
let locationList: Location[] = []

export function extractLocationFromResponse(req: Request): Location {
  const location: Location = {
    id: crypto.randomUUID(),
    name: req.body.location?.name,
    latitude: req.body.location?.latitude,
    longitude: req.body.location?.longitude
  }
  return location;
}

export function setLocation(location: Location) {
  locationList.push(location);
  return;
}

export function getAllLocations() {
  return locationList;
}

router.get('/get', (req: Request, res: Response) => {
  console.log(JSON.stringify(locationList))
  res.json(locationList);
});

router.get('/get/:id', (req: Request, res: Response) => {
  const location = locationList.find((t) => t.id === req.params.id);
  if (!location) {
    res.status(404).send('Location not found');
  } else {
    res.json(location);
  }
});

export default router;
