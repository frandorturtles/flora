// Autorruteador de rejilla para FLORA (2 capas, A*/Dijkstra multi-fuente, holguras reales, GND a plano por vías).
// Entrada: archivo de texto generado por route_pcb.py. Salida: SEG / VIA / FAIL por stdout.
#include <bits/stdc++.h>
using namespace std;

struct Shape { float x0, y0, x1, y1; int net; int lmask; bool pad; };
struct Pad { int id; int net; int lmask; float x0, y0, x1, y1; bool tht; };
static int W, H; static float GX, GY, PITCH;
static vector<uint8_t> allowT[2], allowV[2];
static vector<Shape> shapes;
static vector<Pad> pads;
static float HW = 0.125f, CLR = 0.2f, VR = 0.3f, SAFE = 0.03f;
static int VIA_COST = 500, TURN_COST = 3, BOT_COST = 1;

static inline int IX(float x) { return (int)floorf((x - GX) / PITCH + 0.5f); }
static inline int IY(float y) { return (int)floorf((y - GY) / PITCH + 0.5f); }
static inline float PX(int i) { return GX + i * PITCH; }
static inline float PY(int j) { return GY + j * PITCH; }

static void stamp(vector<uint8_t> &blk, const Shape &s, float m) {
  int i0 = max(0, IX(s.x0 - m) - 1), i1 = min(W - 1, IX(s.x1 + m) + 1);
  int j0 = max(0, IY(s.y0 - m) - 1), j1 = min(H - 1, IY(s.y1 + m) + 1);
  float m2 = m * m;
  for (int j = j0; j <= j1; j++) {
    float py = PY(j); float dy = max(max(s.y0 - py, 0.f), py - s.y1);
    for (int i = i0; i <= i1; i++) {
      float px = PX(i); float dx = max(max(s.x0 - px, 0.f), px - s.x1);
      if (dx * dx + dy * dy < m2) blk[(size_t)j * W + i] = 1;
    }
  }
}

struct Result { vector<array<float, 5>> segs; vector<array<float, 3>> vias; };

int main(int argc, char **argv) {
  FILE *f = fopen(argv[1], "r"); if (!f) return 2;
  char tag[64]; vector<vector<int>> nets; vector<int> netGnd; vector<string> netName;
  string rT, rV;
  while (fscanf(f, "%63s", tag) == 1) {
    string t = tag;
    if (t == "GRID") { fscanf(f, "%f %f %f %d %d", &GX, &GY, &PITCH, &W, &H); }
    else if (t == "PARAMS") { fscanf(f, "%f %f %f %d %d", &HW, &CLR, &VR, &VIA_COST, &TURN_COST); }
    else if (t == "RASTER") { char a[512], b[512]; fscanf(f, "%511s %511s", a, b); rT = a; rV = b; }
    else if (t == "PAD") { Pad p; int tht; fscanf(f, "%d %d %d %f %f %f %f %d", &p.id, &p.net, &p.lmask, &p.x0, &p.y0, &p.x1, &p.y1, &tht); p.tht = tht; pads.push_back(p); }
    else if (t == "NET") { int id, gnd, n; char nm[128]; fscanf(f, "%d %127s %d %d", &id, nm, &gnd, &n); vector<int> v(n); for (auto &x : v) fscanf(f, "%d", &x);
      if ((int)nets.size() <= id) { nets.resize(id + 1); netGnd.resize(id + 1); netName.resize(id + 1); } nets[id] = v; netGnd[id] = gnd; netName[id] = nm; }
  }
  fclose(f);
  size_t N = (size_t)W * H;
  for (int L = 0; L < 2; L++) { allowT[L].resize(N); allowV[L].resize(N); }
  { FILE *g = fopen(rT.c_str(), "rb"); for (int L = 0; L < 2; L++) fread(allowT[L].data(), 1, N, g); fclose(g);
    g = fopen(rV.c_str(), "rb"); for (int L = 0; L < 2; L++) fread(allowV[L].data(), 1, N, g); fclose(g); }
  for (auto &p : pads) shapes.push_back({p.x0, p.y0, p.x1, p.y1, p.net, p.lmask, true});
  float mT = HW + CLR + SAFE, mV = VR + CLR + SAFE, mVown = VR + 0.15f + SAFE;

  // orden: GND al final; resto por longitud estimada
  vector<int> order;
  for (size_t n = 0; n < nets.size(); n++) if (!nets[n].empty() && !netGnd[n]) order.push_back(n);
  auto hpwl = [&](int n) { float a = 1e9, b = -1e9, c = 1e9, d = -1e9; for (int id : nets[n]) { auto &p = pads[id]; float cx = (p.x0 + p.x1) / 2, cy = (p.y0 + p.y1) / 2; a = min(a, cx); b = max(b, cx); c = min(c, cy); d = max(d, cy); } return (b - a) + (d - c); };
  sort(order.begin(), order.end(), [&](int a, int b) { return hpwl(a) < hpwl(b); });
  for (size_t n = 0; n < nets.size(); n++) if (!nets[n].empty() && netGnd[n]) order.push_back(n);

  vector<uint8_t> blkT[2], blkV[2], goal[2];
  vector<int> dist[2]; vector<int> prv[2];
  int failures = 0, nseg = 0, nvia = 0;
  for (int net : order) {
    bool gnd = netGnd[net];
    for (int L = 0; L < 2; L++) {
      blkT[L].assign(N, 0); blkV[L].assign(N, 0); goal[L].assign(N, 0);
      for (size_t k = 0; k < N; k++) { blkT[L][k] = !allowT[L][k]; blkV[L][k] = !allowV[L][k]; }
    }
    for (auto &s : shapes) {
      bool own = (s.net == net);
      for (int L = 0; L < 2; L++) if (s.lmask & (1 << L)) {
        if (!own) { stamp(blkT[L], s, mT); stamp(blkV[L], s, mV); }
        else if (s.pad) stamp(blkV[L], s, mVown);
      }
      if (!own && s.net == -2) {}  // reservado
    }
    // tht propios: los vías no deben caer cerca
    auto padCells = [&](const Pad &p, vector<int> &out, int L) {
      float sx = 0, sy = 0;
      int i0 = IX(p.x0 + sx), i1 = IX(p.x1 - sx), j0 = IY(p.y0 + sy), j1 = IY(p.y1 - sy);
      for (int j = max(0, j0); j <= min(H - 1, j1); j++) for (int i = max(0, i0); i <= min(W - 1, i1); i++) out.push_back(j * W + i);
      (void)L; };
    vector<int> remaining = nets[net]; vector<int> connected;
    auto markPad = [&](const Pad &p) { for (int L = 0; L < 2; L++) if (p.lmask & (1 << L)) { vector<int> c; padCells(p, c, L); for (int k : c) goal[L][k] = 1; } };
    if (gnd) { // los pads THT de GND se consideran ya unidos a los planos
      vector<int> rest; for (int id : remaining) { if (pads[id].tht) { markPad(pads[id]); connected.push_back(id); } else rest.push_back(id); } remaining = rest; }
    else { connected.push_back(remaining[0]); markPad(pads[remaining[0]]); remaining.erase(remaining.begin()); }
    vector<Shape> routeShapes;
    while (!remaining.empty()) {
      // siguiente pad: el más cercano al conjunto conectado (si no hay, el primero)
      int bestK = 0; float bestD = 1e18;
      for (size_t k = 0; k < remaining.size(); k++) { auto &p = pads[remaining[k]]; float cx = (p.x0 + p.x1) / 2, cy = (p.y0 + p.y1) / 2; float d = gnd && connected.empty() ? 0 : 1e18;
        for (int c : connected) { auto &q = pads[c]; float dx = cx - (q.x0 + q.x1) / 2, dy = cy - (q.y0 + q.y1) / 2; d = min(d, dx * dx + dy * dy); } if (d < bestD) { bestD = d; bestK = k; } }
      int pid = remaining[bestK]; auto &P = pads[pid];
      for (int L = 0; L < 2; L++) { dist[L].assign(N, INT_MAX); prv[L].assign(N, -1); }
      typedef pair<int, int> QI; priority_queue<QI, vector<QI>, greater<QI>> pq;
      for (int L = 0; L < 2; L++) if (P.lmask & (1 << L)) { vector<int> c; padCells(P, c, L); bool any = false;
        for (int k : c) if (!blkT[L][k]) { any = true; }
        for (int k : c) if (!any || !blkT[L][k]) { dist[L][k] = 0; pq.push({0, L * (int)N + k}); } }
      int found = -1; bool viaGoal = false;
      static const int dxs[8] = {1, -1, 0, 0, 1, 1, -1, -1}, dys[8] = {0, 0, 1, -1, 1, -1, 1, -1};
      while (!pq.empty()) {
        auto [d, s] = pq.top(); pq.pop(); int L = s / (int)N, k = s % (int)N;
        if (d > dist[L][k]) continue;
        bool viaOk = !blkV[0][k] && !blkV[1][k] && !blkT[0][k] && !blkT[1][k];
        if (goal[L][k] && !(k == -1)) { found = s; break; }
        if (gnd && viaOk && !(P.tht)) { // un vía a los planos GND: no sobre el propio pad
          int i = k % W, j = k / W; bool inPad = false; (void)i; (void)j; if (!inPad) { found = s; viaGoal = true; break; } }
        int i = k % W, j = k / W;
        for (int m = 0; m < 8; m++) {
          int ni = i + dxs[m], nj = j + dys[m]; if (ni < 0 || nj < 0 || ni >= W || nj >= H) continue;
          int nk = nj * W + ni;
          bool diag = m >= 4;
          if (blkT[L][nk] && !goal[L][nk]) continue;
          if (diag && (blkT[L][j * W + ni] || blkT[L][nj * W + i])) continue;
          int c = diag ? 14 : 10; if (L == 1) c += BOT_COST;
          int pm = prv[L][k] >= 0 ? (prv[L][k] % (int)N) : -1; if (pm >= 0) { int pi = pm % W, pj = pm / W; if ((i - pi) != dxs[m] || (j - pj) != dys[m]) c += TURN_COST; }
          int nd = d + c; if (nd < dist[L][nk]) { dist[L][nk] = nd; prv[L][nk] = s; pq.push({nd, L * (int)N + nk}); }
        }
        if (viaOk) { int o = 1 - L; int nd = d + VIA_COST; if (nd < dist[o][k]) { dist[o][k] = nd; prv[o][k] = s; pq.push({nd, o * (int)N + k}); } }
      }
      if (found < 0) { printf("FAIL %s pad %d\n", netName[net].c_str(), pid); failures++; remaining.erase(remaining.begin() + bestK); continue; }
      // reconstruir
      vector<int> path; for (int s = found; s != -1; s = prv[s / (int)N][s % (int)N]) path.push_back(s);
      // path: del goal hacia el pad
      vector<array<float, 3>> pts; // x,y,layer
      for (int s : path) { int L = s / (int)N, k = s % (int)N; pts.push_back({PX(k % W), PY(k / W), (float)L}); }
      // segmentos con fusión colineal
      size_t a = 0;
      while (a + 1 < pts.size()) {
        if (pts[a][2] != pts[a + 1][2]) { printf("VIA %.4f %.4f %d\n", pts[a][0], pts[a][1], net); nvia++;
          routeShapes.push_back({pts[a][0] - VR, pts[a][1] - VR, pts[a][0] + VR, pts[a][1] + VR, net, 3, false});
          for (int L = 0; L < 2; L++) goal[L][IY(pts[a][1]) * W + IX(pts[a][0])] = 1; a++; continue; }
        size_t b = a + 1; float ddx = pts[b][0] - pts[a][0], ddy = pts[b][1] - pts[a][1];
        while (b + 1 < pts.size() && pts[b + 1][2] == pts[a][2] && fabsf((pts[b + 1][0] - pts[b][0]) - ddx) < 1e-4 && fabsf((pts[b + 1][1] - pts[b][1]) - ddy) < 1e-4) b++;
        printf("SEG %d %.4f %.4f %.4f %.4f %d\n", (int)pts[a][2], pts[a][0], pts[a][1], pts[b][0], pts[b][1], net); nseg++;
        for (size_t q = a; q < b; q++) { float x0 = min(pts[q][0], pts[q + 1][0]) - HW, x1 = max(pts[q][0], pts[q + 1][0]) + HW, y0 = min(pts[q][1], pts[q + 1][1]) - HW, y1 = max(pts[q][1], pts[q + 1][1]) + HW;
          routeShapes.push_back({x0, y0, x1, y1, net, 1 << (int)pts[a][2], false}); }
        a = b;
      }
      for (auto &p : pts) goal[(int)p[2]][IY(p[1]) * W + IX(p[0])] = 1;
      if (viaGoal) { // el vía final al plano GND
        auto &e = pts.front(); /* path[0] = found = extremo */ int L = (int)e[2]; (void)L;
        printf("VIA %.4f %.4f %d\n", e[0], e[1], net); nvia++;
        routeShapes.push_back({e[0] - VR, e[1] - VR, e[0] + VR, e[1] + VR, net, 3, false});
        for (int LL = 0; LL < 2; LL++) goal[LL][IY(e[1]) * W + IX(e[0])] = 1; }
      markPad(P); connected.push_back(pid); remaining.erase(remaining.begin() + bestK);
    }
    for (auto &s : routeShapes) shapes.push_back(s);
  }
  printf("DONE %d fallos %d segmentos %d vias\n", failures, nseg, nvia);
  return failures ? 1 : 0;
}
