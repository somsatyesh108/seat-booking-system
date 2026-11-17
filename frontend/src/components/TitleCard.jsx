// TitleCard.jsx - Poster + name + short details. Clicking opens the title's page.

import { Link } from "react-router-dom";
import { priceLabel, subtitleOf } from "../utils";
import Poster from "./Poster";

export default function TitleCard({ item }) {
  const fillingFast = item.seatsLeft > 0 && item.seatsLeft <= 20;

  return (
    <Link to={`/title/${item.slug}`} className="title-card">
      <Poster item={item} />
      <h3>{item.title}</h3>
      <p>{subtitleOf(item)}</p>
      <p>
        {item.language && <>{item.language}, </>}
        {item.minPricePaise !== null && (
          <span className="price">
            {item.minPricePaise === 0 ? "Free" : `from ${priceLabel(item.minPricePaise)}`}
          </span>
        )}
      </p>
      {fillingFast && <p className="filling-fast">Filling fast</p>}
      {item.seatsLeft === 0 && <p className="filling-fast">Sold out</p>}
    </Link>
  );
}