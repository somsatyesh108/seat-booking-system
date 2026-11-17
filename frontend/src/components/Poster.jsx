// Poster.jsx - A gradient "poster" for a title (we don't use real movie images).

import { CATEGORY_ICONS, posterStyle } from "../utils";
import "../styles/cards.css";

export default function Poster({ item }) {
  return (
    <div className="poster" style={posterStyle(item)} aria-hidden="true">
      <div className="poster-top">
        <span className="poster-icon">{CATEGORY_ICONS[item.category]}</span>
        {item.age_rating && <span className="poster-badge">{item.age_rating}</span>}
      </div>
      <span className="poster-title">{item.title}</span>
    </div>
  );
}