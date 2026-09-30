"""MCP server exposing `create_business_trip_application` from business_trip.py."""

from fastmcp import FastMCP

from business_trip import create_business_trip_application

TRAVEL_PLANNING_GUIDE = """\
You are helping fill out a German business-trip application (Dienstreiseantrag).
The applicant is based in Leipzig, Germany. Use the following rules to decide
transport mode, checkboxes, and dates before calling `create_business_trip_application`.
Do not make up information! E.g. if you don't know the applicant's home address, IBAN, 
or other personal details, leave them None or null (not empty string).
You must provide these fields, and you need to reason some of them based on what is 
given by the user:
- destination (at least postal code + city + country, if not in Germany)
- purpose (meeting name or similar)
- departure_date
- departure_time
- business_start_date
- business_start_time
- business_end_date
- business_end_time
- return_date
- return_time

These fields are optional and not required:
- service_unit
- applicant_name
- department": "Antragsteller.Referat",
- office_phone
- home_address
- additional_home_address
- temporary_stay_address
- overnight_cost_per_night          
- private_car_reason (only required if using a private car for traveling)
- flight_reason (only required if using a flight for traveling)
- private_stay_from
- private_stay_until
- private_stay_destination
- iban
- bic
- bank_name
- explanations
- explanations_continuation
- application_date
If the user didn't provide them, do not fill them! Keep them None / null.

## Choosing the transport mode
- Destinations inside Germany, or otherwise reachable comfortably by rail in a few
  hours (e.g. neighbouring countries such as Poland, Czechia, or nearby parts of
  Austria/Netherlands), should use train + public transport for both legs:
  set `outbound_train=True`, `outbound_bus_or_public_transport=True`,
  `return_train=True`, `return_bus_or_public_transport=True`.
- Destinations that are far away, overseas, or would otherwise require a very long
  train ride (roughly more than half a day of travel each way, e.g. most of
  Western/Southern Europe onward, or anywhere outside Europe) should use flight
  instead: set `outbound_flight=True` and `return_flight=True`. Use
  `flight_reason` / `flight_reason_continuation` to justify the choice if asked.
- Only select one primary mode per leg unless additional legs (e.g. bus/public
  transport to/from the airport or station) are genuinely part of the journey.

## Estimating departure and return dates/times
Assume the traveller starts and ends every trip in Leipzig. Before setting
`departure_date`/`departure_time` and `return_date`/`return_time`, estimate the
one-way travel time from Leipzig to the destination (and back):
- Nearby destinations reachable within roughly 2-3 hours (e.g. Dresden, Berlin,
  Halle): same-day travel is fine; departure can be the morning of
  `business_start_date` and return the evening of `business_end_date`.
- Mid-distance destinations requiring roughly half a day of travel each way
  (e.g. Paris, Munich to a far corner of Germany, most of Central Europe by
  train, or a short flight including airport transfer time): if
  `business_start_time` is in the early morning (roughly before 9-10am), the
  traveller cannot arrive in time same-day, so set `departure_date` to the day
  BEFORE `business_start_date` (with an afternoon/evening `departure_time`).
  Otherwise, an early-morning departure on `business_start_date` itself may be
  reasonable. Apply the same logic symmetrically to the return: if
  `business_end_time` is late in the day and travel home would take half a day,
  set `return_date` to the day AFTER `business_end_date`; only keep the return on
  the same day if there is clearly enough remaining time after the business ends.
- Long-distance/overseas destinations reachable only by flight: budget extra
  time for airport transfers, check-in, and connections. Set the departure the
  day before the business start whenever the start time plus necessary travel
  time would not otherwise be reachable, and similarly delay the return by a day
  when the business end time is late.
- When in doubt, prefer arriving with a comfortable buffer (e.g. arriving the
  evening before an early-morning meeting) over risking a missed appointment,
  but avoid padding travel by more than necessary (don't add a full travel day
  for a destination that's only 1-2 hours away).

Note that `departure_date` and `departure_time` must be reasonably BEFORE 
`business_start_date` and `business_start_time`, and `return_date` and `return_time` 
must be reasonably AFTER `business_end_date` and `business_end_time`.    



## General notes
- Dates accepted by the tool are `YYYY-MM-DD` or `DD.MM.YYYY`; times are free text
  (e.g. "08:00").
- Personal fields (home address, IBAN, etc.) fall back to values in `.env` if not
  provided; do not invent these values yourself, ask the user if they are missing
  and not already on file.
- Leave fields unset (do not guess) when information is genuinely unknown; blank
  fields stay empty in the generated PDF for the applicant or office to fill in
  later.
- When the application was created, provide a markdown link to the file, e.g.
  [<filename-and-path-to-pdf>](<filename-and-path-to-pdf>).
"""

mcp = FastMCP(
    name="Business Trip Application",
    instructions=(
        "Fills the applicant-editable fields of the German business-trip "
        "application PDF (Dienstreiseantrag) and saves a completed PDF. "
        "Call the `business_trip_travel_planning_guide` prompt first if you "
        "need help deciding transport mode or travel dates/times."
    ),
)

mcp.tool(
    create_business_trip_application,
    name="create_business_trip_application",
    description=TRAVEL_PLANNING_GUIDE,
)


@mcp.prompt(name="business_trip_travel_planning_guide")
def business_trip_travel_planning_guide() -> str:
    """Guidance for choosing transport mode and estimating travel dates/times."""
    return TRAVEL_PLANNING_GUIDE


if __name__ == "__main__":
    mcp.run()
